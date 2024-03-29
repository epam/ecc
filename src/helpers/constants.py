from enum import Enum

try:
    from http import HTTPMethod  # python3.11+
except ImportError:
    class HTTPMethod(str, Enum):
        HEAD = 'HEAD'
        GET = 'GET'
        POST = 'POST'
        PATCH = 'PATCH'
        DELETE = 'DELETE'
        PUT = 'PUT'

DEFAULT_SYSTEM_CUSTOMER: str = 'SYSTEM'

TESTING_MODE_ENV = 'CUSTODIAN_TESTING'
TESTING_MODE_ENV_TRUE = 'true'

ACTION_PARAM = 'action'
ACTION_PARAM_ERROR = 'There is no handler for the endpoint {endpoint}'

CUSTOMER_ACTION = 'customer'

STANDARD = 'standard'
MITRE = 'mitre'
SERVICE_SECTION = 'service_section'

HTTP_METHOD_ERROR = 'The server does not support the HTTP method {method} ' \
                    'for the resource {resource}'

# Modular:Parent related attributes and types
CUSTODIAN_TYPE = 'CUSTODIAN'  # application that contains access to CUSTODIAN
SCHEDULED_JOB_TYPE = 'SCHEDULED_JOB'
PARENT_ID_ATTR = 'parent_id'
APPLICATION_ID_ATTR = 'application_id'
META_ATTR = 'meta'
TENANT_ENTITY_TYPE = 'TENANT'
VALUE_ATTR = 'value'

SCHEDULE_ATTR = 'schedule'
SCOPE_ATTR = 'scope'
ID_ATTR = 'id'
CUSTOMER_ATTR = 'customer'
USER_CUSTOMER_ATTR = 'user_customer'
TENANT_ATTR = 'tenant'
TENANTS_ATTR = 'tenants'
TENANT_NAMES_ATTR = 'tenant_names'
ACCOUNT_ID_ATTR = 'account_id'
ACCOUNT_ATTR = 'account'
CUSTOMER_DISPLAY_NAME_ATTR = 'customer_display_name'
TENANT_DISPLAY_NAME_ATTR = 'tenant_display_name'
TENANT_DISPLAY_NAMES_ATTR = 'tenant_display_names'
TENANT_NAME_ATTR = 'tenant_name'
CUSTOMER_NAME_ATTR = "customer_name"
RULE_ID_ATTR = 'rule_id'
DISPLAY_NAME_ATTR = 'display_name'
LATEST_LOGIN_ATTR = 'latest_login'
PRIMARY_CONTACTS_ATTR = 'primary_contacts'
SECONDARY_CONTACTS_ATTR = 'secondary_contacts'
TENANT_MANAGER_CONTACTS_ATTR = 'tenant_manager_contacts'
DEFAULT_OWNER_ATTR = 'default_owner'
ACTIVATION_DATE_ATTR = 'activation_date'
INHERIT_ATTR = 'inherit'
CLOUD_ATTR = 'cloud'
CLOUDS_ATTR = 'clouds'
ACCESS_APPLICATION_ID_ATTR = 'access_application_id'
CLOUD_IDENTIFIER_ATTR = 'cloud_identifier'
RULES_TO_EXCLUDE_ATTR = 'rules_to_exclude'
RULES_TO_INCLUDE_ATTR = 'rules_to_include'
REGION_ATTR = 'region'
JOB_ID_ATTR = 'job_id'
LIMIT_ATTR = 'limit'
NEXT_TOKEN_ATTR = 'next_token'
RULE_VERSION_ATTR = 'rule_version'
AWS_CLOUD_ATTR = 'AWS'
AZURE_CLOUD_ATTR = 'AZURE'
# the same, but first is obsolete, second is the one from Maestro's tenants
GCP_CLOUD_ATTR, GOOGLE_CLOUD_ATTR = 'GCP', 'GOOGLE'
KUBERNETES_CLOUD_ATTR = 'KUBERNETES'  # from rules metadata

AZURE_ULTIMATE_REGION = 'AzureCloud'
GOOGLE_ULTIMATE_REGION = 'us-central1'

PERMISSIONS_ATTR = 'permissions'
EXP_ATTR = 'exp'
EXPIRATION_ATTR = 'expiration'

POLICIES_ATTR = 'policies'
NAME_ATTR = 'name'
DESCRIPTION_ATTR = 'description'
IMPACT_ATTR = 'impact'
MIN_CORE_VERSION = 'min_core_version'
SEVERITY_ATTR = 'severity'
VERSION_ATTR = 'version'
FILTERS_ATTR = 'filters'
LOCATION_ATTR = 'location'
COMMENT_ATTR = 'comment'
UPDATED_DATE_ATTR = 'updated_date'
LATEST_SYNC_ATTR = 'latest_sync'
COMMIT_HASH_ATTR = 'commit_hash'
COMMIT_TIME_ATTR = 'commit_time'
SOURCE_ATTR = 'source'
RULES_ATTR = 'rules'
GET_RULES_ATTR = 'get_rules'
RULESETS_ATTR = 'rulesets'
RULES_TO_SCAN_ATTR = 'rules_to_scan'
RULE_SOURCE_ID_ATTR = 'rule_source_id'
S3_PATH_ATTR = 's3_path'
RULES_NUMBER = 'rules_number'
STATUS_ATTR = 'status'
ALL_ATTR = 'all'
GIT_ACCESS_SECRET_ATTR = 'git_access_secret'
GIT_ACCESS_TYPE_ATTR = 'git_access_type'
GIT_PROJECT_ID_ATTR = 'git_project_id'
GIT_REF_ATTR = 'git_ref'
GIT_RULES_PREFIX_ATTR = 'git_rules_prefix'
GIT_URL_ATTR = 'git_url'

STATUS_SYNCING = 'SYNCING'
STATUS_SYNCED = 'SYNCED'
STATUS_SYNCING_FAILED = 'SYNCING_FAILED'

ROLE_ATTR = 'role'
ACTIVE_ATTR = 'active'
EVENT_DRIVEN_ATTR = 'event_driven'
ACTIVE_REGION_STATE = 'ACTIVE'
INACTIVE_REGION_STATE = 'INACTIVE'
POLICIES_TO_ATTACH = 'policies_to_attach'
POLICIES_TO_DETACH = 'policies_to_detach'
PERMISSIONS_TO_ATTACH = 'permissions_to_attach'
PERMISSIONS_TO_DETACH = 'permissions_to_detach'

RULES_TO_ATTACH = 'rules_to_attach'
RULES_TO_DETACH = 'rules_to_detach'

DATA_ATTR = 'data'
CONTENT_ATTR = 'content'
ENABLED = 'enabled'
TRUSTED_ROLE_ARN = 'trusted_role_arn'

TYPE_ATTR = 'type'

ENTITIES_MAPPING_ATTR = 'entities_mapping'
CLEAR_EXISTING_MAPPING_ATTR = 'clear_existing_mapping'
PRODUCT_TYPE_NAME_ATTR = 'product_type_name'
PRODUCT_NAME_ATTR = 'product_name'
ENGAGEMENT_NAME_ATTR = 'engagement_name'
TEST_TITLE_ATTR = 'test_title'
ENTITIES_MAPPING_POSSIBLE_PARAMS = {PRODUCT_TYPE_NAME_ATTR, PRODUCT_NAME_ATTR,
                                    ENGAGEMENT_NAME_ATTR, TEST_TITLE_ATTR}

ALLOWED_FOR_ATTR = 'allowed_for'
RESTRICT_FROM_ATTR = 'restrict_from'
TENANT_ALLOWANCE = 'tenant_allowance'
TENANT_RESTRICTION = 'tenant_restriction'
LICENSED_ATTR = 'licensed'
LICENSE_KEY_ATTR = 'license_key'
LICENSE_KEYS_ATTR = 'license_keys'
LICENSE_KEYS_TO_PREPEND_ATTR = 'license_keys_to_prepend'
LICENSE_KEYS_TO_APPEND_ATTR = 'license_keys_to_append'
LICENSE_KEYS_TO_DETACH_ATTR = 'license_keys_to_detach'
TENANT_LICENSE_KEY_ATTR = 'tenant_license_key'
TENANT_LICENSE_KEYS_ATTR = 'tenant_license_keys'
ATTACHMENT_MODEL_ATTR = 'attachment_model'
CUSTOMERS_ATTR = 'customers'

MAESTRO_USER_ATTR = 'maestro_user'
RABBIT_EXCHANGE_ATTR = 'rabbit_exchange'
REQUEST_QUEUE_ATTR = 'request_queue'
RESPONSE_QUEUE_ATTR = 'response_queue'
SDK_ACCESS_KEY_ATTR = 'sdk_access_key'
CONNECTION_URL_ATTR = 'connection_url'
SDK_SECRET_KEY_ATTR = 'sdk_secret_key'

API_KEY_ATTR = 'api_key'
URL_ATTR = 'url'
AUTO_RESOLVE_ACCESS_ATTR = 'auto_resolve_access'
RESULTS_STORAGE_ATTR = 'results_storage'

# License Manager[Setting].Config:
PORT_ATTR = 'port'
HOST_ATTR = 'host'
# License Manager[Setting].Client:
KEY_ID_ATTR = 'key_id'
ALGORITHM_ATTR = 'algorithm'
PRIVATE_KEY_ATTR = 'private_key'
PUBLIC_KEY_ATTR = 'public_key'
FORMAT_ATTR = 'format'
B64ENCODED_ATTR = 'b64_encoded'

KID_ATTR = 'kid'
ALG_ATTR = 'alg'
TYP_ATTR = 'typ'

START_ATTR = 'start'
END_ATTR = 'end'

CLIENT_TOKEN_ATTR = 'client-token'

GET_URL_ATTR = 'get_url'

CHECK_PERMISSION_ATTR = 'check_permission'

PARAM_USER_ID = 'user_id'
PARAM_REQUEST_PATH = 'path'
PARAM_RESOURCE_PATH = 'resourcePath'
PARAM_HTTP_METHOD = 'httpMethod'
PARAM_CUSTOMER = 'customer'
PARAM_USER_ROLE = 'user_role'
PARAM_USER_CUSTOMER = 'user_customer'

PARAM_ITEMS = 'items'
PARAM_MESSAGE = 'message'
PARAM_TRACE_ID = 'trace_id'
AUTHORIZATION_PARAM = 'authorization'

PARAM_COMPLETE = 'complete'
IDENTIFIER_ATTR = 'identifier'

RULE_SOURCE_REQUIRED_ATTRS = {GIT_PROJECT_ID_ATTR, GIT_URL_ATTR, GIT_REF_ATTR,
                              GIT_RULES_PREFIX_ATTR, GIT_ACCESS_TYPE_ATTR,
                              GIT_ACCESS_SECRET_ATTR}

ENV_VAR_REGION = 'AWS_REGION'

# on-prem
ENV_SERVICE_MODE = 'SERVICE_MODE'
DOCKER_SERVICE_MODE, SAAS_SERVICE_MODE = 'docker', 'saas'

ENV_MONGODB_USER = 'MONGO_USER'
ENV_MONGODB_PASSWORD = 'MONGO_PASSWORD'
ENV_MONGODB_URL = 'MONGO_URL'  # host:port
ENV_MONGODB_DATABASE = 'MONGO_DATABASE'  # custodian_as_a_service

ENV_MINIO_HOST = 'MINIO_HOST'
ENV_MINIO_PORT = 'MINIO_PORT'
ENV_MINIO_ACCESS_KEY = 'MINIO_ACCESS_KEY'
ENV_MINIO_SECRET_ACCESS_KEY = 'MINIO_SECRET_ACCESS_KEY'

ENV_VAULT_TOKEN = 'VAULT_TOKEN'
ENV_VAULT_HOST = 'VAULT_URL'
ENV_VAULT_PORT = 'VAULT_SERVICE_SERVICE_PORT'  # env from Kubernetes

ENV_MAX_NUMBER_OF_JOBS_ON_PREM = 'MAX_NUMBER_OF_JOBS'

# Modular
# Tenant
MODULAR_MANAGEMENT_ID_ATTR = 'management_parent_id'
MODULAR_CLOUD_ATTR = CLOUD_ATTR
MODULAR_DISPLAY_NAME_ATTR = 'display_name'
MODULAR_READ_ONLY_ATTR = 'read_only'
MODULAR_DISPLAY_NAME_TO_LOWER = 'display_name_to_lower'
MODULAR_CONTACTS = 'contacts'
MODULAR_PARENT_MAP = 'parent_map'
# Application
MODULAR_IS_DELETED = 'is_deleted'
MODULAR_DELETION_DATE = 'deletion_date'
MODULAR_SECRET = 'secret'
MODULAR_TYPE = 'type'

# Batch
BATCH_ENV_TENANT_NAME = 'TENANT_NAME'
BATCH_ENV_PLATFORM_ID = 'PLATFORM_ID'
BATCH_ENV_DEFAULT_REPORTS_BUCKET_NAME = 'DEFAULT_REPORTS_BUCKET_NAME'
BATCH_ENV_AWS_REGION = 'AWS_REGION'
BATCH_ENV_CREDENTIALS_KEY = 'CREDENTIALS_KEY'
BATCH_ENV_STATS_S3_BUCKET_NAME = 'STATS_S3_BUCKET_NAME'
BATCH_ENV_VAR_RULESETS_BUCKET_NAME = 'RULESETS_BUCKET_NAME'
BATCH_ENV_JOB_LIFETIME_MIN = 'JOB_LIFETIME_MIN'
BATCH_ENV_MIN_CUSTOM_CORE_VERSION = 'MIN_CUSTOM_CORE_VERSION'
BATCH_ENV_CURRENT_CUSTOM_CORE_VERSION = 'CURRENT_CUSTOM_CORE_VERSION'
BATCH_ENV_EVENT_DRIVEN = 'EVENT_DRIVEN'
BATCH_ENV_LOG_LEVEL = 'LOG_LEVEL'
BATCH_ENV_LM_ACCESS_DATA_HOST = 'LM_ACCESS_DATA_HOST'
BATCH_ENV_SUBMITTED_AT = 'SUBMITTED_AT'
BATCH_ENV_TARGET_REGIONS = 'TARGET_REGIONS'
BATCH_ENV_TARGET_RULESETS = 'TARGET_RULESETS'
BATCH_ENV_TARGET_RULESETS_VIEW = 'TARGET_RULESETS_VIEW'
BATCH_ENV_AFFECTED_LICENSES = 'AFFECTED_LICENSES'
BATCH_ENV_LICENSED_RULESETS = 'LICENSED_RULESETS'
BATCH_ENV_JOB_ID = 'AWS_BATCH_JOB_ID'
BATCH_ENV_SCHEDULED_JOB_NAME = 'SCHEDULED_JOB_NAME'
BATCH_ENV_LM_CLIENT_KEY = 'LM_CLIENT_KEY'
BATCH_ENV_JOB_TYPE = 'JOB_TYPE'
BATCH_ENV_BATCH_RESULTS_ID = 'BATCH_RESULTS_ID'
BATCH_ENV_BATCH_RESULTS_IDS = 'BATCH_RESULTS_IDS'
BATCH_ENV_SYSTEM_CUSTOMER_NAME = 'SYSTEM_CUSTOMER_NAME'

BATCH_STANDARD_JOB_TYPE = 'standard'
BATCH_EVENT_DRIVEN_JOB_TYPE = 'event-driven'
BATCH_MULTI_ACCOUNT_EVENT_DRIVEN_JOB_TYPE = 'event-driven-multi-account'
BATCH_SCHEDULED_JOB_TYPE = 'scheduled'

# CaaSJobs ttl
ENV_VAR_JOBS_TIME_TO_LIVE_DAYS = 'JOBS_TIME_TO_LIVE_DAYS'

# CaaSEvent ttl
ENV_VAR_EVENTS_TTL = 'EVENTS_TTL_HOURS'

ENV_VAR_NUMBER_OF_PARTITIONS_FOR_EVENTS = 'NUMBER_OF_PARTITIONS_FOR_EVENTS'
DEFAULT_NUMBER_OF_PARTITIONS_FOR_EVENTS = 10

ENV_NUMBER_OF_EVENTS_IN_EVENT_ITEM = 'number_of_native_events_in_event_item'
DEFAULT_NUMBER_OF_EVENTS_IN_EVENT_ITEM: int = 100
DEFAULT_EVENTS_TTL_HOURS = 48
DEFAULT_INNER_CACHE_TTL_SECONDS: int = 300

ENV_API_GATEWAY_HOST = 'API_GATEWAY_HOST'
ENV_API_GATEWAY_STAGE = 'API_GATEWAY_STAGE'

ENV_ALLOW_SIMULTANEOUS_JOBS_FOR_ONE_TENANT = \
    'ALLOW_SIMULTANEOUS_JOBS_FOR_ONE_TENANT'
ENV_INNER_CACHE_TTL_SECONDS = 'INNER_CACHE_TTL_SECONDS'

# Batch envs
PARAM_TARGET_RULESETS = 'target_rulesets'
PARAM_RULESET_LICENSE_PRIORITY = 'ruleset_license_priority'
PARAM_RULESET_OVERLAP = 'ruleset_overlap'
PARAM_TARGET_REGIONS = 'target_regions'
PARAM_CREDENTIALS = 'credentials'
PARAM_LICENSED_RULESETS = 'licensed_rulesets'
PARAM_AFFECTED_LICENSES = 'affected_licenses'

# event-driven
AWS_VENDOR = 'AWS'
MAESTRO_VENDOR = 'MAESTRO'

# smtp
USERNAME_ATTR = 'username'
PASSWORD_ATTR = 'password'
DEFAULT_SENDER_ATTR = 'default_sender'
USE_TLS_ATTR = 'use_tls'
MAX_EMAILS_ATTR = 'max_emails'

# Report related attributes
START_ISO_ATTR = 'start_iso'
END_ISO_ATTR = 'end_iso'
HREF_ATTR = 'href'
JSON_ATTR = 'json'
XLSX_ATTR = 'xlsx'
RULE_ATTR = 'rule'

# event statistics
ENV_EVENT_STATISTICS_TYPE = 'event_statistics_type'
EVENT_STATISTICS_TYPE_VERBOSE = 'verbose'
EVENT_STATISTICS_TYPE_SHORT = 'short'

# cred envs
AZURE_TENANT_ID = 'AZURE_TENANT_ID'
AZURE_SUBSCRIPTION_ID = 'AZURE_SUBSCRIPTION_ID'
AZURE_CLIENT_ID = 'AZURE_CLIENT_ID'
AZURE_CLIENT_SECRET = 'AZURE_CLIENT_SECRET'

AWS_ACCESS_KEY_ID = 'AWS_ACCESS_KEY_ID'
AWS_SECRET_ACCESS_KEY = 'AWS_SECRET_ACCESS_KEY'
AWS_DEFAULT_REGION = 'AWS_DEFAULT_REGION'
AWS_SESSION_TOKEN = 'AWS_SESSION_TOKEN'

DEFAULT_REPORTS_BUCKET_NAME = 'reports'
DEFAULT_RULESETS_BUCKET_NAME = 'rulesets'
DEFAULT_SSM_BACKUP_BUCKET_NAME = 'ssm-backup'
DEFAULT_STATISTICS_BUCKET_NAME = 'statistics'
DEFAULT_TEMPLATES_BUCKET_NAME = 'templates'
DEFAULT_METRICS_BUCKET_NAME = 'metrics'
DEFAULT_RECOMMENDATION_BUCKET_NAME = 'recommendation'

PROTOCOL_ATTR = 'protocol'
STAGE_ATTR = 'stage'
API_VERSION_ATTR = 'api_version'
HTTP_ATTR, HTTPS_ATTR = 'HTTP', 'HTTPS'

# reports
DATA_TYPE = 'data_type'
FINDINGS_ATTR = 'findings'
TOTAL_SCANS_ATTR = 'total_scans'
FAILED_SCANS_ATTR = 'failed_scans'
SUCCEEDED_SCANS_ATTR = 'succeeded_scans'
REGIONS_TO_EXCLUDE_ATTR = 'regions_to_exclude'
ACTIVE_ONLY_ATTR = 'active_only'
REPORT_TYPE = 'report_type'
COMPLIANCE_TYPE = 'compliance'
RULE_TYPE = 'rule'
OVERVIEW_TYPE = 'overview'
RESOURCES_TYPE = 'resources'
ATTACK_VECTOR_TYPE = 'attack_vector'
FINOPS_TYPE = 'finops'
OPERATIONAL_REPORT_TYPE = 'operational'
PROJECT_REPORT_TYPE = 'project'
DEPARTMENT_REPORT_TYPE = 'department'
C_LEVEL_REPORT_TYPE = 'c-level'
LAST_SCAN_DATE = 'last_scan_date'
RESOURCE_TYPES_DATA_ATTR = 'resource_types_data'
CURRENT_ATTR = 'current'
SEVERITY_DATA_ATTR = 'severity_data'
ACTIVATED_REGIONS_ATTR = 'activated_regions'
AVERAGE_DATA_ATTR = 'average_data'
END_DATE = 'end_date'
OUTDATED_TENANTS = 'outdated_tenants'

# job status
JOB_SUCCEEDED_STATUS = 'SUCCEEDED'
JOB_FAILED_STATUS = 'FAILED'
JOB_STARTED_STATUS = 'STARTED'
JOB_RUNNABLE_STATUS = 'RUNNABLE'
JOB_RUNNING_STATUS = 'RUNNING'

STATUS_CODE_ATTRS = ('code', 'statusCode', 'StatusCode')

# Maestro Credentials Applications types
AZURE_CREDENTIALS_APP_TYPE = 'AZURE_CREDENTIALS'
AZURE_CERTIFICATE_APP_TYPE = 'AZURE_CERTIFICATE'
AWS_CREDENTIALS_APP_TYPE = 'AWS_CREDENTIALS'
AWS_ROLE_APP_TYPE = 'AWS_ROLE'
GCP_COMPUTE_ACCOUNT_APP_TYPE = 'GCP_COMPUTE_ACCOUNT'
GCP_SERVICE_ACCOUNT_APP_TYPE = 'GCP_SERVICE_ACCOUNT'

CLOUD_TO_APP_TYPE = {
    AWS_CLOUD_ATTR: {
        AWS_CREDENTIALS_APP_TYPE,
        AWS_ROLE_APP_TYPE
    },
    AZURE_CLOUD_ATTR: {
        AZURE_CREDENTIALS_APP_TYPE,
        AZURE_CERTIFICATE_APP_TYPE
    },
    GOOGLE_CLOUD_ATTR: {
        GCP_COMPUTE_ACCOUNT_APP_TYPE,
        GCP_SERVICE_ACCOUNT_APP_TYPE
    }
}

MULTIREGION = 'multiregion'


class HealthCheckStatus(str, Enum):
    OK = 'OK'
    UNKNOWN = 'UNKNOWN'
    NOT_OK = 'NOT_OK'


SPECIFIC_TENANT_SCOPE = 'SPECIFIC_TENANT'
ALL_SCOPE = 'ALL'

DEFAULT_CACHE_LIFETIME = 600  # 10 minutes

# cognito
COGNITO_USERNAME = 'cognito:username'
CUSTOM_ROLE_ATTR = 'custom:role'
CUSTOM_CUSTOMER_ATTR = 'custom:customer'
CUSTOM_LATEST_LOGIN_ATTR = 'custom:latest_login'
CUSTOM_TENANTS_ATTR = 'custom:tenants'

TACTICS_ID_MAPPING = {  # rules do not have tactic IDs
    'Reconnaissance': 'TA0043',
    'Resource Development': 'TA0042',
    'Initial Access': 'TA0001',
    'Execution': 'TA0002',
    'Persistence': 'TA0003',
    'Privilege Escalation': 'TA0004',
    'Defense Evasion': 'TA0005',
    'Credential Access': 'TA0006',
    'Discovery': 'TA0007',
    'Lateral Movement': 'TA0008',
    'Collection': 'TA0009',
    'Exfiltration': 'TA0010',
    'Command and Control': 'TA0011',
    'Impact': 'TA0040'
}

MANUAL_TYPE_ATTR = 'manual'
REACTIVE_TYPE_ATTR = 'reactive'
COMPONENT_NAME_ATTR = 'component_name'

START_DATE = 'start_date'
ARTICLE_ATTR = 'article'

COMPOUND_KEYS_SEPARATOR = '#'

ED_AWS_RULESET_NAME = '_ED_AWS'
ED_AZURE_RULESET_NAME = '_ED_AZURE'
ED_GOOGLE_RULESET_NAME = '_ED_GOOGLE'
ED_KUBERNETES_RULESET_NAME = '_ED_KUBERNETES'


class RuleSourceType(str, Enum):
    GITHUB = 'GITHUB'
    GITLAB = 'GITLAB'


# the next settings are updated automatically when rules meta is pulled.
# They can be set both to s3 and CaaSSettings table. Currently, we set
# them to S3
KEY_RULES_TO_SERVICE_SECTION = 'RULES_TO_SERVICE_SECTION'
KEY_RULES_TO_SEVERITY = 'RULES_TO_SEVERITY'
KEY_RULES_TO_STANDARDS = 'RULES_TO_STANDARDS'
KEY_RULES_TO_MITRE = 'RULES_TO_MITRE'
KEY_CLOUD_TO_RULES = 'CLOUD_TO_RULES'
KEY_HUMAN_DATA = 'HUMAN_DATA'
KEY_RULES_TO_SERVICE = 'RULES_TO_SERVICE'
KEY_RULES_TO_CATEGORY = 'RULES_TO_CATEGORY'
KEY_AWS_STANDARDS_COVERAGE = 'AWS_STANDARDS_COVERAGE'
KEY_AZURE_STANDARDS_COVERAGE = 'AZURE_STANDARDS_COVERAGE'
KEY_GOOGLE_STANDARDS_COVERAGE = 'GOOGLE_STANDARDS_COVERAGE'
KEY_AWS_EVENTS = 'AWS_EVENTS'
KEY_AZURE_EVENTS = 'AZURE_EVENTS'
KEY_GOOGLE_EVENTS = 'GOOGLE_EVENTS'


class PlatformType(str, Enum):
    EKS = 'EKS'
    NATIVE = 'NATIVE'
