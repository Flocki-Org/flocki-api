import logging
import tempfile

import boto3
from botocore.exceptions import ClientError
from starlette.responses import FileResponse


class S3Utils:
    def __init__(self, bucket_name, region=None, access_key=None, secret_access_key=None):
        self.bucket_name = bucket_name
        self.s3 = boto3.resource('s3', aws_access_key_id=access_key, aws_secret_access_key=secret_access_key, region_name=region)


    def upload_file(self, file, object_name=None):
        try:
            response = self.s3.meta.client.upload_fileobj (file, self.bucket_name, object_name)
        except ClientError as e:
            logging.error(e)
            return False
        except Exception as e:
            logging.error(e)
            return False
        return True

    def get_file(self, object_name):
        try:
            obj = self.s3.Object(self.bucket_name, key=object_name).get()
            #convert obj to StreamingResponse
            return obj
        except Exception as e:
            logging.error(e)
            raise e

    def delete_file(self, object_name):
        try:
            response = self.s3.Object(self.bucket_name, object_name).delete()
        except ClientError as e:
            logging.error(e)
            return False
        return True

    def list_files(self):
        try:
            response = self.bucket.objects.all()
        except ClientError as e:
            logging.error(e)
            return False
        return response