import operator
from enum import Enum


# from http import HTTPMethod  # python3.11+


class HTTPMethod(str, Enum):
    HEAD = 'HEAD'
    GET = 'GET'
    POST = 'POST'
    PATCH = 'PATCH'
    DELETE = 'DELETE'
    PUT = 'PUT'


class CustodianEndpoint(str, Enum):
    """
    Should correspond to Api gateway models
    """
    DOC = '/doc'
    JOBS = '/jobs'
    ROLES = '/roles'
    RULES = '/rules'
    USERS = '/users'
    EVENT = '/event'
    SIGNIN = '/signin'
    SIGNUP = '/signup'
    HEALTH = '/health'
    REFRESH = '/refresh'
    TENANTS = '/tenants'
    RULESETS = '/rulesets'
    LICENSES = '/licenses'
    POLICIES = '/policies'
    JOBS_K8S = '/jobs/k8s'
    CUSTOMERS = '/customers'
    HEALTH_ID = '/health/{id}'
    JOBS_JOB = '/jobs/{job_id}'
    DOC_PROXY = '/doc/{proxy+}'
    ROLES_NAME = '/roles/{name}'
    CREDENTIALS = '/credentials'
    META_META = '/rule-meta/meta'
    RULE_SOURCES = '/rule-sources'
    USERS_WHOAMI = '/users/whoami'
    SCHEDULED_JOB = '/scheduled-job'
    PLATFORMS_K8S = '/platforms/k8s'
    SETTINGS_MAIL = '/settings/mail'
    JOBS_STANDARD = '/jobs/standard'
    BATCH_RESULTS = '/batch-results'
    REPORTS_RETRY = '/reports/retry'
    POLICIES_NAME = '/policies/{name}'
    METRICS_STATUS = '/metrics/status'
    REPORTS_CLEVEL = '/reports/clevel'
    METRICS_UPDATE = '/metrics/update'
    REPORTS_STATUS = '/reports/status'
    REPORTS_PROJECT = '/reports/project'
    USERS_USERNAME = '/users/{username}'
    CREDENTIALS_ID = '/credentials/{id}'
    RULE_SOURCES_ID = '/rule-sources/{id}'
    RULESETS_RELEASE = '/rulesets/release'
    ED_RULESETS = '/rulesets/event-driven'
    DOC_SWAGGER_JSON = '/doc/swagger.json'
    META_STANDARDS = '/rule-meta/standards'
    RULE_META_UPDATER = '/rules/update-meta'
    REPORTS_PUSH_DOJO = '/reports/push/dojo'
    CUSTOMERS_RABBITMQ = '/customers/rabbitmq'
    REPORTS_DIAGNOSTIC = '/reports/diagnostic'
    REPORTS_DEPARTMENT = '/reports/department'
    INTEGRATIONS_SELF = '/integrations/temp/sre'
    SCHEDULED_JOB_NAME = '/scheduled-job/{name}'
    REPORTS_OPERATIONAL = '/reports/operational'
    TENANTS_TENANT_NAME = '/tenants/{tenant_name}'
    USERS_RESET_PASSWORD = '/users/reset-password'
    REPORTS_EVENT_DRIVEN = '/reports/event_driven'
    RULE_SOURCES_ID_SYNC = '/rule-sources/{id}/sync'
    LICENSES_LICENSE_KEY = '/licenses/{license_key}'
    SETTINGS_SEND_REPORTS = '/settings/send_reports'
    PLATFORMS_K8S_ID = '/platforms/k8s/{platform_id}'
    INTEGRATIONS_CHRONICLE = '/integrations/chronicle'
    CREDENTIALS_ID_BINDING = '/credentials/{id}/binding'
    CUSTOMERS_EXCLUDED_RULES = '/customers/excluded-rules'
    INTEGRATIONS_DEFECT_DOJO = '/integrations/defect-dojo'
    REPORTS_PUSH_DOJO_JOB_ID = '/reports/push/dojo/{job_id}'
    INTEGRATIONS_CHRONICLE_ID = '/integrations/chronicle/{id}'
    REPORTS_RULES_JOBS_JOB_ID = '/reports/rules/jobs/{job_id}'
    BATCH_RESULTS_JOB_ID = '/batch-results/{batch_results_id}'
    LICENSES_LICENSE_KEY_SYNC = '/licenses/{license_key}/sync'
    REPORTS_ERRORS_JOBS_JOB_ID = '/reports/errors/jobs/{job_id}'
    INTEGRATIONS_DEFECT_DOJO_ID = '/integrations/defect-dojo/{id}'
    REPORTS_DIGESTS_JOBS_JOB_ID = '/reports/digests/jobs/{job_id}'
    REPORTS_DETAILS_JOBS_JOB_ID = '/reports/details/jobs/{job_id}'
    TENANTS_TENANT_NAME_REGIONS = '/tenants/{tenant_name}/regions'
    REPORTS_FINDINGS_JOBS_JOB_ID = '/reports/findings/jobs/{job_id}'
    REPORTS_PUSH_CHRONICLE_JOB_ID = '/reports/push/chronicle/{job_id}'
    REPORTS_RESOURCES_JOBS_JOB_ID = '/reports/resources/jobs/{job_id}'
    REPORTS_COMPLIANCE_JOBS_JOB_ID = '/reports/compliance/jobs/{job_id}'
    SETTINGS_LICENSE_MANAGER_CLIENT = '/settings/license-manager/client'
    SETTINGS_LICENSE_MANAGER_CONFIG = '/settings/license-manager/config'
    LICENSE_LICENSE_KEY_ACTIVATION = '/licenses/{license_key}/activation'
    REPORTS_RULES_TENANTS_TENANT_NAME = '/reports/rules/tenants/{tenant_name}'
    TENANTS_TENANT_NAME_EXCLUDED_RULES = '/tenants/{tenant_name}/excluded-rules'
    TENANTS_TENANT_NAME_ACTIVE_LICENSES = '/tenants/{tenant_name}/active-licenses'
    INTEGRATIONS_CHRONICLE_ID_ACTIVATION = '/integrations/chronicle/{id}/activation'
    REPORTS_COMPLIANCE_TENANTS_TENANT_NAME = '/reports/compliance/tenants/{tenant_name}'
    INTEGRATIONS_DEFECT_DOJO_ID_ACTIVATION = '/integrations/defect-dojo/{id}/activation'
    REPORTS_DETAILS_TENANTS_TENANT_NAME_JOBS = '/reports/details/tenants/{tenant_name}/jobs'
    REPORTS_DIGESTS_TENANTS_TENANT_NAME_JOBS = '/reports/digests/tenants/{tenant_name}/jobs'
    REPORTS_FINDINGS_TENANTS_TENANT_NAME_JOBS = '/reports/findings/tenants/{tenant_name}/jobs'
    REPORTS_PUSH_CHRONICLE_TENANTS_TENANT_NAME = '/reports/push/chronicle/tenants/{tenant_name}'
    REPORTS_RESOURCES_TENANTS_TENANT_NAME_JOBS = '/reports/resources/tenants/{tenant_name}/jobs'
    REPORTS_RAW_TENANTS_TENANT_NAME_STATE_LATEST = '/reports/raw/tenants/{tenant_name}/state/latest'
    REPORTS_RESOURCES_TENANTS_TENANT_NAME_LATEST = '/reports/resources/tenants/{tenant_name}/state/latest'
    REPORTS_RESOURCES_PLATFORMS_K8S_PLATFORM_ID_LATEST = '/reports/resources/platforms/k8s/{platform_id}/state/latest'


LAMBDA_INVOCATION_TRACE_ID_HEADER = 'Lambda-Invocation-Trace-Id'
SERVER_VERSION_HEADER = 'Accept-Version'


class ParentScope(str, Enum):
    ALL = 'ALL'
    DISABLED = 'DISABLED'
    SPECIFIC = 'SPECIFIC'

    @classmethod
    def iter(cls):
        return map(operator.attrgetter('value'), cls)


AWS, AZURE, GCP, GOOGLE = 'AWS', 'AZURE', 'GCP', 'GOOGLE'
KUBERNETES = 'KUBERNETES'
# This tuple represent clouds types of rules/rulesets, not tenants or jobs
RULE_CLOUDS = (AWS, AZURE, GCP, KUBERNETES)

DATA_ATTR = 'data'
ITEMS_ATTR = 'items'
ERRORS_ATTR = 'errors'
MESSAGE_ATTR = 'message'
NEXT_TOKEN_ATTR = 'next_token'

C7NCLI_LOG_LEVEL_ENV_NAME = 'SRE_CLI_LOG_LEVEL'
C7NCLI_DEVELOPER_MODE_ENV_NAME = 'SRE_CLI_DEVELOPER_MODE'


class JobType(str, Enum):
    MANUAL = 'manual'
    REACTIVE = 'reactive'


# Credentials
ENV_AWS_ACCESS_KEY_ID = 'AWS_ACCESS_KEY_ID'
ENV_AWS_SECRET_ACCESS_KEY = 'AWS_SECRET_ACCESS_KEY'
ENV_AWS_SESSION_TOKEN = 'AWS_SESSION_TOKEN'
ENV_AWS_DEFAULT_REGION = 'AWS_DEFAULT_REGION'
ENV_AWS_REGION = 'AWS_REGION'

ENV_AZURE_TENANT_ID = 'AZURE_TENANT_ID'
ENV_AZURE_SUBSCRIPTION_ID = 'AZURE_SUBSCRIPTION_ID'
ENV_AZURE_CLIENT_ID = 'AZURE_CLIENT_ID'
ENV_AZURE_CLIENT_SECRET = 'AZURE_CLIENT_SECRET'

ENV_GOOGLE_APPLICATION_CREDENTIALS = 'GOOGLE_APPLICATION_CREDENTIALS'

DEFAULT_AWS_REGION = 'us-east-1'

# responses
NO_ITEMS_TO_DISPLAY_RESPONSE_MESSAGE = 'No items to display'
NO_CONTENT_RESPONSE_MESSAGE = 'Request is successful. No content returned'  # 204

CONFIG_FOLDER = '.c7n'

CONTEXT_MODULAR_ADMIN_USERNAME = 'modular_admin_username'

CONF_ACCESS_TOKEN = 'access_token'
CONF_REFRESH_TOKEN = 'refresh_token'
CONF_API_LINK = 'api_link'
CONF_ITEMS_PER_COLUMN = 'items_per_column'

MODULE_NAME = 'c7n'  # for modular admin


class JobState(str, Enum):
    """
    https://docs.aws.amazon.com/batch/latest/userguide/job_states.html
    """
    SUBMITTED = 'SUBMITTED'
    PENDING = 'PENDING'
    RUNNABLE = 'RUNNABLE'
    STARTING = 'STARTING'
    RUNNING = 'RUNNING'
    FAILED = 'FAILED'
    SUCCEEDED = 'SUCCEEDED'

    @classmethod
    def iter(cls):
        return map(operator.attrgetter('value'), cls)


class PolicyErrorType(str, Enum):
    """
    For statistics
    """
    SKIPPED = 'SKIPPED'
    ACCESS = 'ACCESS'  # not enough permissions
    CREDENTIALS = 'CREDENTIALS'  # invalid credentials
    CLIENT = 'CLIENT'  # some other client error
    INTERNAL = 'INTERNAL'  # unexpected error

    @classmethod
    def iter(cls):
        return map(operator.attrgetter('value'), cls)


class ModularCloud(str, Enum):
    AZURE = 'AZURE'
    YANDEX = 'YANDEX'
    GOOGLE = 'GOOGLE'
    AWS = 'AWS'
    OPENSTACK = 'OPEN_STACK'
    CSA = 'CSA'
    HWU = 'HARDWARE'
    ENTERPRISE = 'ENTERPRISE'
    EXOSCALE = 'EXOSCALE'
    WORKSPACE = 'WORKSPACE'
    AOS = 'AOS'
    VSPHERE = 'VSPHERE'
    VMWARE = 'VMWARE'  # VCloudDirector group
    NUTANIX = 'NUTANIX'

    @classmethod
    def iter(cls):
        return map(operator.attrgetter('value'), cls)
