"""
[Up-to-date description]

Available environment variables:
- ...
- ...

Usage: python executor.py

Exit codes:
- 0: success;
- 1: unexpected system error;
- 2: Job execution is not granted by the License Manager;
- 126: Job is event-driven and cannot be executed in consequence of invalid
  credentials or conceivably some other temporal reason. Retry is allowed.
"""
import os
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
import io
from itertools import chain
import operator
from pathlib import Path
import sys
import tempfile
import multiprocessing
import time
import traceback
from typing import Generator, cast

import msgspec.json
from botocore.exceptions import ClientError
from c7n.config import Config
from c7n.exceptions import PolicyValidationError
from c7n.policy import Policy, PolicyCollection
from c7n.provider import clouds
from c7n.resources import load_resources
from google.auth.exceptions import GoogleAuthError
from googleapiclient.errors import HttpError
from modular_sdk.commons.constants import ENV_KUBECONFIG, ParentType
from modular_sdk.models.parent import Parent
from modular_sdk.models.tenant import Tenant
from modular_sdk.services.environment_service import EnvironmentContext
from msrestazure.azure_exceptions import CloudError

from executor.helpers.constants import (
    ACCESS_DENIED_ERROR_CODE,
    AWS_DEFAULT_REGION,
    CACHE_FILE,
    ExecutorError,
    INVALID_CREDENTIALS_ERROR_CODES,
    ENV_AWS_DEFAULT_REGION,
)
from executor.helpers.profiling import BytesEmitter, xray_recorder as _XRAY
from executor.services import BSP
from services.clients.lm_client import LMException
from executor.services.policy_service import PolicyDict
from executor.services.report_service import JobResult
from helpers.constants import (
    BatchJobEnv,
    BatchJobType,
    Cloud,
    GLOBAL_REGION,
    JobState,
    PlatformType,
    PolicyErrorType,
    TS_EXCLUDED_RULES_KEY,
    CAASEnv
)
from helpers.log_helper import get_logger
from helpers.time_helper import utc_datetime, utc_iso
from models.batch_results import BatchResults
from models.job import Job
from models.rule import RuleIndex
from models.scheduled_job import ScheduledJob
from services import SP
from services.ambiguous_job_service import AmbiguousJob
from services.clients import Boto3ClientFactory
from services.clients.dojo_client import DojoV2Client
from services.clients.eks_client import EKSClient
from services.clients.sts import TokenGenerator, StsClient
from services.job_lock import TenantSettingJobLock
from services.job_service import JobUpdater, NullJobUpdater
from services.platform_service import K8STokenKubeconfig, Kubeconfig, Platform
from services.chronicle_service import ChronicleConverterType
from services.udm_generator import ShardCollectionUDMEntitiesConvertor, ShardCollectionUDMEventsConvertor
from services.ruleset_service import RulesetName
from services.report_convertors import ShardCollectionDojoConvertor
from services.reports_bucket import (
    PlatformReportsBucketKeysBuilder,
    StatisticsBucketKeysBuilder,
    TenantReportsBucketKeysBuilder,
)
from services.clients.chronicle import ChronicleV2Client
from services.sharding import ShardsCollection, ShardsCollectionFactory, ShardsS3IO

_LOG = get_logger(__name__)


class ExecutorException(Exception):
    def __init__(self, error: ExecutorError):
        self.error = error


def get_time_left() -> float:
    _LOG.debug('Retrieving job time threshold')
    if BSP.environment_service.is_docker():
        _LOG.debug('On prem job - using current timestamp as start time')
        started_at = utc_datetime().timestamp() * 1e3
    else:
        _LOG.debug('Saas - using AWS Batch startedAt attribute')
        job = SP.batch.get_job(BSP.environment_service.batch_job_id())
        started_at = job.get('startedAt') or utc_datetime().timestamp() * 1e3

    threshold = datetime.timestamp(
        datetime.fromtimestamp(started_at / 1e3) + timedelta(
            minutes=BSP.environment_service.job_lifetime_min())
    )
    _LOG.debug(f'Threshold: {threshold}, {datetime.fromtimestamp(threshold)}')
    return threshold


TIME_THRESHOLD: float = get_time_left()


class PoliciesLoader:
    __slots__ = ('_cloud', '_output_dir', '_regions', '_cache', 
                 '_cache_period', '_load_global')

    def __init__(self, cloud: Cloud, output_dir: Path,
                 regions: set[str] | None = None, cache: str = CACHE_FILE,
                 cache_period: int = 30, load_global: bool = True):
        """
        :param cloud:
        :param output_dir:
        :param regions:
        :param cache:
        :param cache_period:
        """
        self._cloud = cloud
        self._output_dir = output_dir
        self._regions = regions or set()
        if self._cloud != Cloud.AWS and self._regions:
            _LOG.warning(f'Given regions will be ignored because the cloud is '
                         f'{self._cloud}')
        self._cache = cache
        self._cache_period = cache_period
        self._load_global = load_global

    def set_global_output(self, policy: Policy) -> None:
        policy.options.output_dir = str(
            (self._output_dir / GLOBAL_REGION).resolve()
        )

    def set_regional_output(self, policy: Policy) -> None:
        policy.options.output_dir = str(
            (self._output_dir / policy.options.region).resolve()
        )

    @staticmethod
    def is_global(policy: Policy) -> bool:
        """
        Tells whether this policy must be executed only once ignoring its
        region
        :param policy:
        :return:
        """
        if policy.provider_name != 'aws':
            return True

        if comment := policy.data.get('comment'):
            return RuleIndex(comment).is_global
        rt = policy.resource_manager.resource_type
        # s3 has one endpoint for all regions
        return rt.global_resource or rt.service == 's3'

    @staticmethod
    def get_policy_region(policy: Policy) -> str:
        if PoliciesLoader.is_global(policy):
            return GLOBAL_REGION
        return policy.options.region

    def _base_config(self) -> Config:
        """
        Probably, most fields not even used when we load, but just keep them
        :return:
        """
        match self._cloud:
            case Cloud.AWS:
                # load for all and just keep necessary. It does not provide
                # much overhead but more convenient
                regions = ['all']
            case Cloud.AZURE:
                regions = ['AzureCloud']
            case _:
                regions = []
        return Config.empty(
            regions=regions,
            cache=self._cache,
            cache_period=self._cache_period,
            command='c7n.commands.run',
            config=None,
            configs=[],
            output_dir=str(self._output_dir),
            subparser='run',
            policy_filters=[],
            resource_types=[],
            verbose=None,
            quiet=False,
            debug=False,
            skip_validation=False,
            vars=None
        )

    @staticmethod
    def _get_resource_types(policies: list[PolicyDict]) -> set[str]:
        res = set()
        for pol in policies:
            rtype = pol['resource']
            if isinstance(rtype, list):
                res.update(rtype)
            elif '.' not in rtype:
                rtype = f'aws.{rtype}'
            res.add(rtype)
        return res

    def prepare_policies(self, policies: list[Policy],
                         ) -> Generator[Policy, None, None]:
        """
        Keeps only policies with regions that must be scanned. Also keeps
        global policies and changes their output_dir to global.
        Exceptions:
        - s3, region-dependent, but API is global. So treat like global.
          No need to make requests multiple times
        - waf, global but its
          resource_manager.resource_type.global_resource == False.
          Though it's not global in resource_type class, Cloud Custodian
          treats it like global and loads only once because
          boto3.Session().get_available_regions('waf') returns an empty list
        :param policies:
        :return:
        """
        global_yielded = set()
        n_global, n_not_global = 0, 0
        for policy in policies:
            if self._load_global and self.is_global(policy):
                if policy.name in global_yielded:
                    # custom core loads all the global policies only once
                    # (except S3 which technically is not global).
                    continue
                _LOG.debug(f'Global policy found: {policy.name}')
                self.set_global_output(policy)
                policy.options.region = AWS_DEFAULT_REGION
                policy.session_factory.region = AWS_DEFAULT_REGION
                global_yielded.add(policy.name)
                n_global += 1
            elif not self._regions or policy.options.region in self._regions:
                _LOG.debug(f'Not global policy found: {policy.name}')
                n_not_global += 1
                # self.set_regional_output(policy)  # Cloud Custodian does it
            else:
                continue
            yield policy
        _LOG.debug(f'Global policies: {n_global}')
        _LOG.debug(f'Not global policies: {n_not_global}')

    def _load(self, policies: list[PolicyDict],
              options: Config | None = None) -> list[Policy]:
        """
        Unsafe load using internal CLoud Custodian API:
        - does not load file, we already have policies list
        - does not check duplicates, can be sure there are no them
        - we almost can be sure there are all 100% valid. We should just skip
          invalid instead of throwing SystemError
        - don't need Structure parser from Cloud Custodian
        - don't need schema validation
        - don't need filters from config and some other things
        :param policies:
        :return:
        """
        if not options:
            options = self._base_config()
        options.region = ''
        load_resources(self._get_resource_types(policies))
        # here we should probably validate schema, but it's too time-consuming
        provider_policies = {}
        for policy in policies:
            try:
                pol = Policy(policy, options)
            except PolicyValidationError:
                _LOG.warning(f'Cannot load policy {policy["name"]} '
                             f'dict to object. Skipping', exc_info=True)
                continue
            provider_policies.setdefault(pol.provider_name, []).append(pol)

        # initialize providers (copied from Cloud Custodian)
        collection = PolicyCollection.from_data({}, options)
        for provider_name in provider_policies:
            provider = clouds[provider_name]()
            p_options = provider.initialize(options)
            collection += provider.initialize_policies(
                PolicyCollection(provider_policies[provider_name], p_options),
                p_options
            )

        # Variable expansion and non schema validation
        result = []
        for p in collection:
            p.expand_variables(p.get_variables())
            try:
                p.validate()
            except PolicyValidationError as e:
                _LOG.warning(f'Policy {p.name} validation failed',
                             exc_info=True)
                continue
            except (ValueError, Exception):
                _LOG.warning('Unexpected error occurred validating policy',
                             exc_info=True)
                continue
            result.append(p)
        return result

    def load_from_policies(self, policies: list[PolicyDict]) -> list[Policy]:
        """
        This functionality is already present inside Cloud Custodian but that
        is that part of private python API, besides it does more that we need.
        So, this is our small implementation which does exactly what we need
        here.
        :param policies:
        :return:
        """
        _LOG.info('Loading policies')
        items = self._load(policies)
        match self._cloud:
            case Cloud.AWS:
                items = list(self.prepare_policies(items))
            case _:
                for pol in items:
                    self.set_global_output(pol)
        _LOG.info('Policies were loaded')
        return items

    def load_from_regions_to_rules(self, policies: list[PolicyDict],
                                   mapping: dict[str, set[str]]
                                   ) -> list[Policy]:
        """
        Expected mapping:
        {
            'eu-central-1': {'epam-aws-005..', 'epam-aws-006..'},
            'eu-west-1': {'epam-aws-006..', 'epam-aws-007..'}
        }
        :param policies:
        :param mapping:
        :return:
        """
        rules = set(chain.from_iterable(mapping.values()))  # all rules
        if self._cloud != Cloud.AWS:
            # load all policies ignoring region and set global to all
            items = self._load(policies)
            items = list(filter(lambda p: p.name in rules, items))
            for policy in items:
                self.set_global_output(policy)
            return items
        # self._cloud == Cloud.AWS
        # first -> I load all the rules for regions that came + us-east-1.
        # second -> execute self.prepare_policies in order to set global
        # third -> For each region I keep only necessary rules
        config = self._base_config()
        config.regions = [*mapping.keys(), AWS_DEFAULT_REGION]
        items = []
        for policy in self.prepare_policies(self._load(policies, config)):
            if self.is_global(policy) and policy.name in rules:
                items.append(policy)
            elif policy.name in (mapping.get(policy.options.region) or ()):
                items.append(policy)
        return items


class Runner(ABC):
    cloud: Cloud | None = None

    def __init__(self, policies: list[Policy], failed: dict | None = None):
        self._policies = policies

        self._failed = failed or {}

        self._is_ongoing = False
        self._error_type: PolicyErrorType = PolicyErrorType.SKIPPED  # default
        self._message = None
        self._exception = None

    @classmethod
    def factory(cls, cloud: Cloud, policies: list[Policy],
                failed: dict | None = None) -> 'Runner':
        """
        Builds a necessary runner instance based on cloud.
        :param cloud:
        :param policies:
        :param failed:
        :return:
        """
        # TODO refactor, make runner not abstract and move policy
        #  error handling (depending on policy's cloud) to a separate class
        _class = next(
            filter(lambda sub: sub.cloud == cloud, cls.__subclasses__())
        )
        return _class(policies, failed)

    @property
    def failed(self) -> dict:
        return self._failed

    @_XRAY.capture('Run policies consistently')
    def start(self):
        self._is_ongoing = True
        while self._policies:
            self._handle_errors(policy=self._policies.pop(0))
        self._is_ongoing = False

    def _call_policy(self, policy: Policy):
        if TIME_THRESHOLD <= utc_datetime().timestamp():
            if self._is_ongoing:
                _LOG.warning('Job time threshold has been exceeded. '
                             'All the consequent rules will be skipped.')
            self._is_ongoing = False
            self._error_type = PolicyErrorType.SKIPPED
            self._message = ('Job time exceeded the maximum '
                             'possible execution time')
        if not self._is_ongoing:
            self._add_failed(
                region=PoliciesLoader.get_policy_region(policy),
                policy=policy.name,
                error_type=self._error_type,
                message=self._message,
                exception=self._exception
            )
            return
        policy()

    @staticmethod
    def add_failed(failed: dict, region: str, policy: str,
                   error_type: PolicyErrorType,
                   exception: Exception | None = None,
                   message: str | None = None):
        tb = []
        if exception:
            te = traceback.TracebackException.from_exception(exception)
            tb.extend(te.format())
            if not message:
                message = ''.join(te.format_exception_only())
        failed[(region, policy)] = (error_type, message, tb)

    def _add_failed(self, region: str, policy: str,
                    error_type: PolicyErrorType, 
                    exception: Exception | None = None,
                    message: str | None = None):
        self.add_failed(self._failed, region, policy, error_type, exception,
                        message)

    @abstractmethod
    def _handle_errors(self, policy: Policy):
        ...


class AWSRunner(Runner):
    cloud = Cloud.AWS

    def _handle_errors(self, policy: Policy):
        name, region = policy.name, PoliciesLoader.get_policy_region(policy)
        try:
            self._call_policy(policy)
        except ClientError as error:
            error_code = error.response.get('Error', {}).get('Code')
            error_reason = error.response.get('Error', {}).get('Message')

            if error_code in ACCESS_DENIED_ERROR_CODE.get(self.cloud):
                _LOG.warning(f'Policy \'{name}\' is skipped. '
                             f'Reason: \'{error_reason}\'')
                self._add_failed(
                    region=region, policy=name,
                    error_type=PolicyErrorType.ACCESS,
                    message=error_reason
                )
            elif error_code in INVALID_CREDENTIALS_ERROR_CODES.get(self.cloud):
                _LOG.warning(
                    f'Policy \'{name}\' is skipped due to invalid '
                    f'credentials. All the subsequent rules will be skipped')
                self._add_failed(
                    region=region, policy=name,
                    error_type=PolicyErrorType.CREDENTIALS,
                    message=error_reason
                )
                self._is_ongoing = False
                self._error_type = PolicyErrorType.CREDENTIALS
                self._message = error_reason
            else:
                _LOG.warning(f'Policy \'{name}\' has failed. '
                             f'Client error occurred. '
                             f'Code: \'{error_code}\'. '
                             f'Reason: {error_reason}')
                self._add_failed(
                    region=region, policy=name,
                    error_type=PolicyErrorType.CLIENT,
                    exception=error
                )
        except Exception as error:
            _LOG.exception(f'Policy {name} has failed with unexpected error')
            self._add_failed(
                region=region, policy=name,
                error_type=PolicyErrorType.INTERNAL,
                exception=error
            )


class AZURERunner(Runner):
    cloud = Cloud.AZURE

    def _handle_errors(self, policy: Policy):
        name, region = policy.name, PoliciesLoader.get_policy_region(policy)
        try:
            self._call_policy(policy)
        except CloudError as error:
            error_code = error.error
            error_reason = error.message.split(':')[-1].strip()
            if error_code in INVALID_CREDENTIALS_ERROR_CODES.get(self.cloud):
                _LOG.warning(
                    f'Policy \'{name}\' is skipped due to invalid '
                    f'credentials. All the subsequent rules will be skipped')
                self._add_failed(
                    region=region, policy=name,
                    error_type=PolicyErrorType.CREDENTIALS,
                    message=error_reason
                )
                self._is_ongoing = False
                self._error_type = PolicyErrorType.CREDENTIALS
                self._message = error_reason
            else:
                _LOG.warning(f'Policy \'{name}\' has failed. '
                             f'Client error occurred. '
                             f'Code: \'{error_code}\'. '
                             f'Reason: {error_reason}')
                self._add_failed(
                    region=region, policy=name,
                    error_type=PolicyErrorType.CLIENT,
                    exception=error
                )
        except Exception as error:
            _LOG.exception(f'Policy {name} has failed with unexpected error')
            self._add_failed(
                region=region, policy=name,
                error_type=PolicyErrorType.INTERNAL,
                exception=error
            )


class GCPRunner(Runner):
    cloud = Cloud.GOOGLE

    def _handle_errors(self, policy: Policy):
        name, region = policy.name, PoliciesLoader.get_policy_region(policy)
        try:
            self._call_policy(policy)
        except GoogleAuthError as error:
            error_reason = str(error.args[-1])
            _LOG.warning(
                f'Policy \'{name}\' is skipped due to invalid '
                f'credentials. All the subsequent rules will be skipped')
            self._add_failed(
                region=region, policy=name,
                error_type=PolicyErrorType.CREDENTIALS,
                message=error_reason
            )
            self._is_ongoing = False
            self._error_type = PolicyErrorType.CREDENTIALS
            self._message = error_reason
        except HttpError as error:
            if error.status_code == 403:
                self._add_failed(
                    region=region, policy=name,
                    error_type=PolicyErrorType.ACCESS,
                    message=error.reason
                )
            else:
                self._add_failed(
                    region=region, policy=name,
                    error_type=PolicyErrorType.CLIENT,
                    exception=error
                )
        except Exception as error:
            _LOG.exception(f'Policy {name} has failed with unexpected error')
            self._add_failed(
                region=region, policy=name,
                error_type=PolicyErrorType.INTERNAL,
                exception=error
            )


class K8SRunner(Runner):
    cloud = Cloud.KUBERNETES

    def _handle_errors(self, policy: Policy):
        name, region = policy.name, PoliciesLoader.get_policy_region(policy)
        try:
            self._call_policy(policy)
        except Exception as error:
            _LOG.exception(f'Policy {name} has failed with unexpected error')
            self._add_failed(
                region=region,
                policy=name,
                error_type=PolicyErrorType.INTERNAL,
                exception=error
            )


def fetch_licensed_ruleset_list(tenant: Tenant, licensed: dict):
    """
    Designated to execute preliminary licensed Job instantiation, which
    verifies permissions to create a demanded entity.
    :parameter tenant: Tenant of the issuer
    :parameter licensed: Dict - non-empty collection of licensed rulesets
    :raises: ExecutorException - given parameter absence or prohibited action
    :return: List[Dict]
    """
    job_id = BSP.environment_service.job_id()

    _LOG.debug(f'Going to license a Job:\'{job_id}\'.')

    try:
        licensed_job = SP.license_manager_service.cl.post_job(
            job_id=job_id,
            customer=tenant.customer_name,
            tenant=tenant.name,
            ruleset_map=licensed
        )
    except LMException as e:
        ExecutorError.LM_DID_NOT_ALLOW.reason = str(e)
        raise ExecutorException(ExecutorError.LM_DID_NOT_ALLOW)

    _LOG.info(f'Job {job_id} was allowed')
    content = licensed_job['ruleset_content']
    return [dict(
        id=ruleset_id,
        licensed=True,
        s3_path=source,
        active=True,
        status=dict(code='READY_TO_SCAN')
    ) for ruleset_id, source in content.items()]


@_XRAY.capture('Fetch licensed ruleset')
def get_licensed_ruleset_dto_list(tenant: Tenant, job: Job) -> list[dict]:
    """
    Preliminary step, given an affected license and respective ruleset(s),
    can raise
    """
    licensed, standard = [], []
    for r in map(RulesetName, job.rulesets):
        if r.license_key:
            licensed.append(r)
        else:
            standard.append(r)
    if not licensed:
        return []
    license_key = licensed[0].license_key
    rulesets = [RulesetName(r.name, r.version, None) for r in licensed]
    lic = SP.license_service.get_nullable(license_key)
    rulesets = fetch_licensed_ruleset_list(
        tenant=tenant, licensed={
            lic.tenant_license_key(tenant.customer_name): [r.to_str() for r in rulesets]
        }
    )
    # LM returns rulesets of specific versions even if we don't specify
    # versions. The code below just updates job's rulesets with valid versions
    licensed = [RulesetName(i['id']) for i in rulesets]
    _LOG.debug(f'Licensed rulesets are fetched: {licensed}')
    SP.job_service.update(job, rulesets=[s.to_str() for s in standard] + [
        RulesetName(i.name, i.version, license_key).to_str() for i in licensed
    ])
    return rulesets


@_XRAY.capture('Upload to SIEM')
def upload_to_siem(tenant: Tenant, collection: ShardsCollection,
                   job: AmbiguousJob, platform: Platform | None = None):
    for dojo, configuration in SP.integration_service.get_dojo_adapters(tenant, True):
        convertor = ShardCollectionDojoConvertor.from_scan_type(
            configuration.scan_type
        )
        configuration = configuration.substitute_fields(job, platform)
        client = DojoV2Client(
            url=dojo.url,
            api_key=SP.defect_dojo_service.get_api_key(dojo)
        )
        try:
            client.import_scan(
                scan_type=configuration.scan_type,
                scan_date=utc_datetime(),
                product_type_name=configuration.product_type,
                product_name=configuration.product,
                engagement_name=configuration.engagement,
                test_title=configuration.test,
                data=convertor.convert(collection),
                tags=SP.integration_service.job_tags_dojo(job)
            )
        except Exception:
            _LOG.exception('Unexpected error occurred pushing to dojo')
    mcs = SP.modular_client.maestro_credentials_service()
    for chronicle, configuration in SP.integration_service.get_chronicle_adapters(tenant, True):
        _LOG.debug('Going to push data to Chronicle')
        creds = mcs.get_by_application(
            chronicle.credentials_application_id,
            tenant
        )
        if not creds:
            continue
        client = ChronicleV2Client(
            url=chronicle.endpoint,
            credentials=creds.GOOGLE_APPLICATION_CREDENTIALS,
            customer_id=chronicle.instance_customer_id
        )
        match configuration.converter_type:
            case ChronicleConverterType.EVENTS:
                _LOG.debug('Converting our collection to UDM events')
                convertor = ShardCollectionUDMEventsConvertor(tenant=tenant)
                client.create_udm_events(events=convertor.convert(collection))
            case _:  # ENTITIES
                _LOG.debug('Converting our collection to UDM entities')
                convertor = ShardCollectionUDMEntitiesConvertor(tenant=tenant)
                success = client.create_udm_entities(
                    entities=convertor.convert(collection),
                    log_type='AWS_API_GATEWAY'  # todo use a generic log type or smt
                )


@_XRAY.capture('Get credentials')
def get_credentials(tenant: Tenant,
                    batch_results: BatchResults | None = None) -> dict:
    """
    Tries to retrieve credentials to scan the given tenant with such
    priorities:
    1. env "CREDENTIALS_KEY" - gets key name and then gets credentials
       from SSM. This is the oldest solution, in can sometimes be used if
       the job is standard and a user has given credentials directly;
       The SSM parameter is removed after the creds are received.
    2. Only for event-driven jobs. Gets credentials_key (SSM parameter name)
       from "batch_result.credentials_key". Currently, the option is obsolete.
       API in no way will set credentials key there. But maybe some time...
    3. 'CUSTODIAN_ACCESS' key in the tenant's parent_map. It points to the
       parent with type 'CUSTODIAN_ACCESS' as well. That parent is linked
       to an application with credentials
    4. Maestro management_parent_id -> management creds. Tries to resolve
       management parent from tenant and then management credentials. This
       option can be used only if the corresponding env is set to 'true'.
       Must be explicitly allowed because the option is not safe.
    5. Checks whether instance by default has access to the given tenant
    If not credentials are found, ExecutorException is raised
    """
    mcs = SP.modular_client.maestro_credentials_service()
    _log_start = 'Trying to get credentials from '
    credentials = {}
    # 1.
    if not credentials:
        _LOG.info(_log_start + '\'CREDENTIALS_KEY\' env')
        credentials = BSP.credentials_service.get_credentials_from_ssm()
        if credentials and tenant.cloud == Cloud.GOOGLE:
            credentials = BSP.credentials_service.google_credentials_to_file(
                credentials)
    # 2.
    if not credentials and batch_results and batch_results.credentials_key:
        _LOG.info(_log_start + 'batch_results.credentials_key')
        credentials = BSP.credentials_service.get_credentials_from_ssm(
            batch_results.credentials_key)
        if credentials and tenant.cloud == Cloud.GOOGLE:
            credentials = BSP.credentials_service.google_credentials_to_file(
                credentials)
    # 3.
    if not credentials:
        _LOG.info(_log_start + '`CUSTODIAN_ACCESS` parent')
        parent = SP.modular_client.parent_service().get_linked_parent_by_tenant(
            tenant=tenant,
            type_=ParentType.CUSTODIAN_ACCESS
        )
        if parent:
            application = SP.modular_client.application_service().get_application_by_id(parent.application_id)
            if application:
                _creds = mcs.get_by_application(application, tenant)
                if _creds:
                    credentials = _creds.dict()
    # 4.
    if not credentials and BSP.environment_service.is_management_creds_allowed():
        _LOG.info(_log_start + 'Maestro management parent & application')
        _creds = mcs.get_by_tenant(tenant=tenant)
        if _creds:  # not a dict
            credentials = _creds.dict()
    # 5
    if not credentials:
        _LOG.info(_log_start + 'instance profile')
        # TODO refactor
        match tenant.cloud:
            case Cloud.AWS:
                try:
                    aid = StsClient.factory().build().get_caller_identity()['Account']
                    _LOG.debug('Instance profile found')
                    if aid == tenant.project:
                        _LOG.info('Instance profile credentials match to tenant id')
                        return {}
                except (Exception, ClientError) as e:
                    _LOG.warning(f'No instance credentials found: {e}')
            case Cloud.AZURE:
                try:
                    from c7n_azure.session import Session
                    aid = Session().subscription_id
                    _LOG.info('subscription id found')
                    if aid == tenant.project:
                        _LOG.info('Subscription id matches to tenant id')
                        return {}
                except BaseException:  # catch sys.exit(1)
                    _LOG.warning('Could not find azure subscription id')
    if credentials:
        credentials = mcs.complete_credentials_dict(
            credentials=credentials,
            tenant=tenant
        )
        return credentials
    raise ExecutorException(ExecutorError.NO_CREDENTIALS)


def get_platform_credentials(platform: Platform) -> dict:
    """
    Credentials for platform (k8s) only. This should be refactored somehow.
    Raises ExecutorException if not credentials are found
    :param platform:
    :return:
    """
    # TODO K8S request a short-lived token here from long-lived in case
    #  it's possible
    # if creds.token:
    #     _LOG.info('Request a temp token')
    #     conf = kubernetes.client.Configuration()
    #     conf.host = creds.endpoint
    #     conf.api_key['authorization'] = creds.token
    #     conf.api_key_prefix['authorization'] = 'Bearer'
    #     conf.ssl_ca_cert = creds.ca_file()
    #     kubernetes.client.AuthenticationV1TokenRequest()
    #     with kubernetes.client.ApiClient(conf) as client:
    #         kubernetes.client.CoreV1Api(client).create_namespaced_service_account_token('readonly-user')
    app = SP.modular_client.application_service().get_application_by_id(
        platform.parent.application_id
    )
    token = BSP.credentials_service.get_credentials_from_ssm()
    kubeconfig = {}
    if app.secret:
        kubeconfig = SP.modular_client.assume_role_ssm_service().get_parameter(
            app.secret) or {}  # noqa

    if kubeconfig and token:
        _LOG.debug('Kubeconfig and custom token are provided. '
                   'Combining both')
        config = Kubeconfig(kubeconfig)
        session = str(int(time.time()))
        user = f'user-{session}'
        context = f'context-{session}'
        cluster = next(config.cluster_names())  # always should be 1 at least

        config.add_user(user, token)
        config.add_context(context, cluster, user)
        config.current_context = context
        return {ENV_KUBECONFIG: str(config.to_temp_file())}
    elif kubeconfig:
        _LOG.debug('Only kubeconfig is provided')
        config = Kubeconfig(kubeconfig)
        return {ENV_KUBECONFIG: str(config.to_temp_file())}
    if platform.type != PlatformType.EKS:
        _LOG.warning('No kubeconfig provided and platform is not EKS')
        raise ExecutorException(ExecutorError.NO_CREDENTIALS)
    _LOG.debug('Kubeconfig and token are not provided. '
               'Using management creds for EKS')
    tenant = SP.modular_client.tenant_service().get(platform.tenant_name)
    parent = SP.modular_client.parent_service().get_linked_parent_by_tenant(
        tenant=tenant, type_=ParentType.AWS_MANAGEMENT
    )
    if not parent:
        _LOG.warning('Parent AWS_MANAGEMENT not found')
        raise ExecutorException(ExecutorError.NO_CREDENTIALS)
    application = SP.modular_client.application_service().get_application_by_id(parent.application_id)
    if not application:
        _LOG.warning('Management application is not found')
        raise ExecutorException(ExecutorError.NO_CREDENTIALS)
    creds = SP.modular_client.maestro_credentials_service().get_by_application(
        application, tenant
    )
    if not creds:
        _LOG.warning(f'No credentials in '
                     f'application: {application.application_id}')
        raise ExecutorException(ExecutorError.NO_CREDENTIALS)
    cluster = EKSClient.factory().from_keys(
        aws_access_key_id=creds.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=creds.AWS_SECRET_ACCESS_KEY,
        aws_session_token=creds.AWS_SESSION_TOKEN,
        region_name=platform.region
    ).describe_cluster(platform.name)
    if not cluster:
        _LOG.error(f'No cluster with name: {platform.name} '
                   f'in region: {platform.region}')
        raise ExecutorException(ExecutorError.NO_CREDENTIALS)
    sts = Boto3ClientFactory('sts').from_keys(
        aws_access_key_id=creds.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=creds.AWS_SECRET_ACCESS_KEY,
        aws_session_token=creds.AWS_SESSION_TOKEN,
        region_name=AWS_DEFAULT_REGION
    )
    token_config = K8STokenKubeconfig(
        endpoint=cluster['endpoint'],
        ca=cluster['certificateAuthority']['data'],
        token=TokenGenerator(sts).get_token(platform.name)
    )
    return {ENV_KUBECONFIG: str(token_config.to_temp_file())}


@_XRAY.capture('Get rules to exclude')
def get_rules_to_exclude(tenant: Tenant) -> set[str]:
    """
    Takes into consideration rules that are excluded for that specific tenant
    and for its customer
    :param tenant:
    :return:
    """
    _LOG.info('Querying excluded rules')
    excluded = set()
    ts = SP.modular_client.tenant_settings_service().get(
        tenant_name=tenant.name,
        key=TS_EXCLUDED_RULES_KEY
    )
    if ts:
        _LOG.info('Tenant setting with excluded rules is found')
        excluded.update(ts.value.as_dict().get('rules') or ())
    cs = SP.modular_client.customer_settings_service().get_nullable(
        customer_name=tenant.customer_name,
        key=TS_EXCLUDED_RULES_KEY
    )
    if cs:
        _LOG.info('Customer setting with excluded rules is found')
        excluded.update(cs.value.get('rules') or ())
    return excluded


@_XRAY.capture('Batch results job')
def batch_results_job(batch_results: BatchResults):
    _XRAY.put_annotation('batch_results_id', batch_results.id)

    temp_dir = tempfile.TemporaryDirectory()
    work_dir = Path(temp_dir.name)

    tenant: Tenant = SP.modular_client.tenant_service().get(batch_results.tenant_name)
    cloud = Cloud[tenant.cloud.upper()]
    credentials = get_credentials(tenant, batch_results)

    policies = BSP.policies_service.separate_ruleset(
        from_=BSP.policies_service.ensure_event_driven_ruleset(cloud),
        exclude=get_rules_to_exclude(tenant),
        keep=set(
            chain.from_iterable(batch_results.regions_to_rules().values())
        )
    )
    loader = PoliciesLoader(
        cloud=cloud,
        output_dir=work_dir,
        regions=BSP.environment_service.target_regions()
    )
    with EnvironmentContext(credentials, reset_all=False):
        runner = Runner.factory(cloud, loader.load_from_regions_to_rules(
            policies,
            batch_results.regions_to_rules()
        ))
        runner.start()

    result = JobResult(work_dir, cloud)
    keys_builder = TenantReportsBucketKeysBuilder(tenant)
    collection = ShardsCollectionFactory.from_cloud(cloud)
    collection.put_parts(result.iter_shard_parts())
    meta = result.rules_meta()
    collection.meta = meta

    _LOG.info('Going to upload to SIEM')
    upload_to_siem(
        tenant=tenant,
        collection=collection,
        job=AmbiguousJob(batch_results),
    )

    collection.io = ShardsS3IO(
        bucket=SP.environment_service.default_reports_bucket_name(),
        key=keys_builder.ed_job_result(batch_results),
        client=SP.s3
    )
    _LOG.debug('Writing job report')
    collection.write_all()  # writes job report

    latest = ShardsCollectionFactory.from_cloud(cloud)
    latest.io = ShardsS3IO(
        bucket=SP.environment_service.default_reports_bucket_name(),
        key=keys_builder.latest_key(),
        client=SP.s3
    )
    _LOG.debug('Pulling latest state')
    latest.fetch_by_indexes(collection.shards.keys())
    latest.fetch_meta()

    difference = collection - latest

    _LOG.debug('Writing latest state')
    latest.update(collection)
    latest.update_meta(meta)
    latest.write_all()
    latest.write_meta()

    _LOG.debug('Writing difference')
    difference.io = ShardsS3IO(
        bucket=SP.environment_service.default_reports_bucket_name(),
        key=keys_builder.ed_job_difference(batch_results),
        client=SP.s3
    )
    difference.write_all()

    _LOG.info('Writing statistics')
    SP.s3.gz_put_json(
        bucket=SP.environment_service.get_statistics_bucket_name(),
        key=StatisticsBucketKeysBuilder.job_statistics(batch_results),
        obj=result.statistics(tenant, runner.failed)
    )
    temp_dir.cleanup()


def multi_account_event_driven_job() -> int:
    for br_uuid in BSP.environment_service.batch_results_ids():
        _LOG.info(f'Processing batch results with id {br_uuid}')
        actions = []
        batch_results = BatchResults.get_nullable(br_uuid)
        if not batch_results:
            _LOG.warning('Somehow batch results item does not exist. Skipping')
            continue
        if batch_results.status == JobState.SUCCEEDED.value:
            _LOG.info('Batch results already succeeded. Skipping')
            continue
        try:
            _LOG.info(f'Starting job for batch result')
            batch_results_job(batch_results)
            _LOG.info(f'Job for batch result {br_uuid} has finished')
            actions.append(BatchResults.status.set(JobState.SUCCEEDED.value))
        except ExecutorException as e:
            _LOG.exception(f'Executor exception {e.error} occurred')
            actions.append(BatchResults.status.set(JobState.FAILED.value))
            actions.append(BatchResults.reason.set(traceback.format_exc()))
        except Exception:
            _LOG.exception('Unexpected exception occurred')
            actions.append(BatchResults.status.set(JobState.FAILED.value))
            actions.append(BatchResults.reason.set(traceback.format_exc()))
        actions.append(BatchResults.stopped_at.set(utc_iso()))
        _LOG.info('Saving batch results item')
        batch_results.update(actions=actions)
    Path(CACHE_FILE).unlink(missing_ok=True)
    return 0


def update_scheduled_job() -> None:
    """
    Updates 'last_execution_time' in scheduled job item if
    this is a scheduled job.
    """
    _LOG.info('Updating scheduled job item in DB')
    scheduled_job_name = BSP.env.scheduled_job_name()
    if not scheduled_job_name:
        _LOG.info('The job is not scheduled. No scheduled job '
                  'item to update. Skipping')
        return
    _LOG.info('The job is scheduled. Updating the '
              '\'last_execution_time\' in scheduled job item')
    item = ScheduledJob(id=scheduled_job_name, type=ScheduledJob.default_type)
    item.update(actions=[ScheduledJob.last_execution_time.set(utc_iso())])


def single_account_standard_job() -> int:
    # in case it's a standard job , tenant_name will always exist
    tenant_name = cast(str, BSP.env.tenant_name())
    tenant = cast(Tenant, SP.modular_client.tenant_service().get(tenant_name))

    if job_id := BSP.env.job_id():
        # custodian job id, present only for standard jobs
        job = cast(Job, SP.job_service.get_nullable(job_id))
        if BSP.env.is_docker():
            updater = JobUpdater(job)
        else:
            updater = NullJobUpdater(job)  # updated in caas-job-updater
    else:  # scheduled job, generating it dynamically
        scheduled = ScheduledJob.get_nullable(BSP.env.scheduled_job_name())
        updater = JobUpdater.from_batch_env(
            environment=dict(os.environ),
            rulesets=scheduled.context.scan_rulesets
        )
        updater.save()
        job = updater.job
        BSP.env.override_environment({BatchJobEnv.CUSTODIAN_JOB_ID.value: job.id})

    if BSP.env.is_scheduled():  # locking scanned regions
        TenantSettingJobLock(tenant_name).acquire(
            job_id=job.id,
            regions=BSP.env.target_regions() or {GLOBAL_REGION}
        )
        update_scheduled_job()

    updater.created_at = utc_iso()
    updater.started_at = utc_iso()
    updater.status = JobState.RUNNING
    updater.update()

    temp_dir = tempfile.TemporaryDirectory()

    try:
        standard_job(job, tenant, Path(temp_dir.name))
        updater.status = JobState.SUCCEEDED
        updater.stopped_at = utc_iso()
        code = 0
    except ExecutorException as e:
        _LOG.exception(f'Executor exception {e.error} occurred')
        # in case the job has failed, we should update it here even if it's
        # saas installation because we cannot retrieve traceback from
        # caas-job-updater lambda
        updater = JobUpdater.from_job_id(job.id)
        updater.status = JobState.FAILED
        updater.stopped_at = utc_iso()
        updater.reason = e.error.with_reason()
        match e.error:
            case ExecutorError.LM_DID_NOT_ALLOW:
                code = 2
            case _:
                code = 1
    except Exception:
        _LOG.exception('Unexpected error occurred')
        updater = JobUpdater.from_job_id(job.id)
        updater.status = JobState.FAILED
        updater.stopped_at = utc_iso()
        updater.reason = ExecutorError.INTERNAL
        code = 1
    finally:
        Path(CACHE_FILE).unlink(missing_ok=True)
        TenantSettingJobLock(tenant_name).release(job.id)
        temp_dir.cleanup()

    updater.update()

    if BSP.env.is_docker() and BSP.env.is_licensed_job():
        _LOG.info('The job is licensed on premises. Updating in LM')
        SP.license_manager_service.cl.update_job(
            job_id=job.id,
            customer=job.customer_name,
            created_at=job.created_at,
            started_at=job.started_at,
            stopped_at=job.stopped_at,
            status=job.status
        )
    return code


def process_job(filename: str, work_dir: Path, cloud: Cloud,
                q: multiprocessing.Queue,
                region: str = GLOBAL_REGION):
    """
    Cloud Custodian keeps consuming RAM for some reason. After 9th-10th region
    scanned the used memory can be more than 1GI, and it does get free. Not
    sure about correctness and legality of this workaround, but it
    seems to help. We execute scan for each region in a separate process
    consequently. When one process finished its memory is freed
    (any way the results is flushed to files).
    """
    with open(filename, 'rb') as file:
        data = msgspec.json.decode(file.read())
    loader = PoliciesLoader(
        cloud=cloud,
        output_dir=work_dir,
        regions={region},
        # not to be confused, if regions=={'global'} any region will be skipped because 'global' is just a not valid region name
        cache_period=120,
        load_global=region == GLOBAL_REGION
    )
    try:
        _LOG.debug('Loading policies')
        policies = loader.load_from_policies(data)
        _LOG.info(f'{len(policies)} were loaded')
        runner = Runner.factory(cloud, policies)
        _LOG.info('Starting runner')
        runner.start()
        _LOG.info('Runner has finished')
        q.put(runner.failed)
    except Exception:  # not considered
        # TODO this exception can occur if, say, credentials are invalid.
        #  In such a case PolicyErrorType.CREDENTIALS won't be assigned to
        #  those policies that should've been executed here. Must be fixed
        _LOG.exception('Unexpected error occurred trying to scan')
        q.put({})


@_XRAY.capture('Standard job')
def standard_job(job: Job, tenant: Tenant, work_dir: Path):
    cloud: Cloud  # not cloud but rather domain
    platform: Platform | None = None
    if pid := BSP.env.platform_id():
        parent = cast(
            Parent, 
            SP.modular_client.parent_service().get_parent_by_id(pid)
        )
        platform = Platform(parent)
        cloud = Cloud.KUBERNETES
    else:
        cloud = Cloud[tenant.cloud.upper()]

    _LOG.info(f'{BSP.env.job_type().capitalize()} job \'{job.id}\' '
              f'has started: {cloud=}, {tenant.name=}, {platform=}')
    _LOG.debug(f'Entire sys.argv: {sys.argv}')
    _LOG.debug(f'Environment: {BSP.env}')
    _XRAY.put_annotation('job_id', job.id)
    _XRAY.put_annotation('tenant_name', tenant.name)
    _XRAY.put_metadata('cloud', cloud.value)

    if platform:
        credentials = get_platform_credentials(platform)
    else:
        credentials = get_credentials(tenant)

    licensed_urls = map(operator.itemgetter('s3_path'),
                        get_licensed_ruleset_dto_list(tenant, job))
    standard_urls = map(SP.ruleset_service.download_url,
                        BSP.policies_service.get_standard_rulesets(job))

    policies = BSP.policies_service.get_policies(
        urls=chain(licensed_urls, standard_urls),
        keep=set(job.rules_to_scan),
        exclude=get_rules_to_exclude(tenant)
    )
    with tempfile.NamedTemporaryFile(delete=False) as file:
        file.write(msgspec.json.encode(policies))
    failed = {}
    with EnvironmentContext(credentials, reset_all=False):
        q = multiprocessing.Queue()
        for region in [GLOBAL_REGION, ] + sorted(BSP.env.target_regions()):
            p = multiprocessing.Process(
                target=process_job,
                args=(file.name, work_dir, cloud, q, region)
            )
            p.start()
            _LOG.info(f'Starting Cloud Custodian process for {region} with pid {p.pid}')
            _LOG.info(f'Waiting for item from queue')
            failed.update(q.get())
            p.join()
            p.close()

    result = JobResult(work_dir, cloud)
    if platform:
        keys_builder = PlatformReportsBucketKeysBuilder(platform)
    else:
        keys_builder = TenantReportsBucketKeysBuilder(tenant)

    collection = ShardsCollectionFactory.from_cloud(cloud)
    collection.put_parts(result.iter_shard_parts())
    meta = result.rules_meta()
    collection.meta = meta

    _LOG.info('Going to upload to SIEM')
    upload_to_siem(tenant=tenant, collection=collection,
                   job=AmbiguousJob(job), platform=platform)

    collection.io = ShardsS3IO(
        bucket=SP.environment_service.default_reports_bucket_name(),
        key=keys_builder.job_result(job),
        client=SP.s3
    )

    _LOG.debug('Writing job report')
    collection.write_all()  # writes job report

    latest = ShardsCollectionFactory.from_cloud(cloud)
    latest.io = ShardsS3IO(
        bucket=SP.environment_service.default_reports_bucket_name(),
        key=keys_builder.latest_key(),
        client=SP.s3
    )

    _LOG.debug('Pulling latest state')
    latest.fetch_by_indexes(collection.shards.keys())
    latest.fetch_meta()

    _LOG.debug('Writing latest state')
    latest.update(collection)
    latest.update_meta(meta)
    latest.write_all()
    latest.write_meta()

    _LOG.info('Writing statistics')
    SP.s3.gz_put_json(
        bucket=SP.environment_service.get_statistics_bucket_name(),
        key=StatisticsBucketKeysBuilder.job_statistics(job),
        obj=result.statistics(tenant, failed)
    )
    _LOG.info(f'Job \'{job.id}\' has ended')


def main(command: list[str] | None = None, environment: dict | None = None):
    env = environment or {}
    env.setdefault(ENV_AWS_DEFAULT_REGION, AWS_DEFAULT_REGION)
    BSP.environment_service.override_environment(env)

    buffer = io.BytesIO()
    _XRAY.configure(emitter=BytesEmitter(buffer))  # noqa

    _XRAY.begin_segment('AWS Batch job')
    sampled = _XRAY.is_sampled()
    _LOG.info(f'Batch job is {"" if sampled else "NOT "}sampled')
    _XRAY.put_annotation('batch_job_id', BSP.env.batch_job_id())

    match BSP.environment_service.job_type():
        case BatchJobType.EVENT_DRIVEN:
            _LOG.info('Starting event driven job')
            code = multi_account_event_driven_job()
        case _:  # BatchJobType.STANDARD | BatchJobType.SCHEDULED
            _LOG.info('Starting standard job')
            code = single_account_standard_job()

    _XRAY.end_segment()

    if sampled:
        _LOG.debug('Writing xray data to S3')
        buffer.seek(0)
        SP.s3.gz_put_object(
            bucket=SP.environment_service.get_statistics_bucket_name(),
            key=StatisticsBucketKeysBuilder.xray_log(BSP.env.batch_job_id()),
            body=buffer
        )
    _LOG.info('Finished')
    sys.exit(code)


if __name__ == '__main__':
    main(command=sys.argv)
