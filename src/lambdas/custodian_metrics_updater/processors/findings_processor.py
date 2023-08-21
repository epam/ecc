from datetime import timedelta

from helpers import get_logger
from helpers.constants import DATA_TYPE, START_DATE
from helpers.time_helper import utc_datetime
from services import SERVICE_PROVIDER
from services.clients.s3 import S3Client
from services.environment_service import EnvironmentService

_LOG = get_logger(__name__)
NEXT_STEP = 'recommendations'


class FindingsUpdater:
    def __init__(self, s3_client: S3Client,
                 environment_service: EnvironmentService):
        self.s3_client = s3_client
        self.environment_service = environment_service
        self.today = utc_datetime(utc=False).date().isoformat()
        self.yesterday = (utc_datetime(utc=False) -
                          timedelta(days=1)).date().isoformat()

    def process_data(self, event):
        bucket = self.environment_service.get_statistics_bucket_name()
        yesterday_findings_path = f'findings/{self.yesterday}/'
        today_findings_path = f'findings/{self.today}/'
        objects = list(self.s3_client.list_objects(
            bucket_name=bucket, prefix=yesterday_findings_path
        ))

        _LOG.debug(f'Retrieved objects (first attempt): {objects}')
        if not objects:
            objects = [o for o in self.s3_client.list_objects(
                bucket_name=bucket, prefix='findings')
                       if o.get('Key').endswith('json.gz') or o.get('Key').
                       endswith('json')]
            _LOG.debug(f'Retrieved objects (second attempt): {objects}')

        for obj in objects:
            file = obj.get('Key')
            today_filename = f'{today_findings_path}{file.split("/")[-1]}'
            if self.s3_client.file_exists(bucket, today_filename):
                _LOG.debug(f'File {today_filename} already exists, skipping..')
                continue

            _LOG.debug(f'Update file {file}')
            content = self.s3_client.get_file_content(
                bucket_name=bucket, full_file_name=file)
            self.s3_client.put_object(
                bucket_name=bucket,
                object_name=today_filename,
                body=content)

        return {DATA_TYPE: NEXT_STEP, START_DATE: event.get(START_DATE),
                'continuously': event.get('continuously')}


FINDINGS_UPDATER = FindingsUpdater(
    s3_client=SERVICE_PROVIDER.s3(),
    environment_service=SERVICE_PROVIDER.environment_service()
)
