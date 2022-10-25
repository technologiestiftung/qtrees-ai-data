import boto3
from botocore.exceptions import ClientError
from .helper import get_logger

logger = get_logger(name="AWS UTIL", level="INFO")


def upload_file(filename, bucket_name, obj_key=None):
    """Upload a file to an S3 bucket

    :param filename: File to upload
    :param bucket_name: Bucket to upload to
    :param obj_key: S3 object name. If not specified then filename is used
    :return: True if file was uploaded, else False
    """

    # If S3 obj_key was not specified, use filename
    if obj_key is None:
        obj_key = filename

    # Upload the file
    s3_client = boto3.client('s3')
    try:
        logger.info('uploading to bucket')
        s3_client.upload_file(filename, bucket_name, obj_key)
    except ClientError as e:
        logger.error(e)
        return False
    return True


def download_file(filename, bucket_name, obj_key):
    s3_client = boto3.client('s3')
    try:
        logger.info('downloading from bucket')
        s3_client.download_file(bucket_name, obj_key, filename)
    except ClientError as e:
        logger.error(e)
        return False
    return True


def delete_obj(bucket_name, obj_key):
    s3_client = boto3.client('s3')
    try:
        s3_client.delete_object(Bucket=bucket_name, Key=obj_key)
    except ClientError:
        logger.info(f"obj with key {obj_key} not found")
        return False
    return True
