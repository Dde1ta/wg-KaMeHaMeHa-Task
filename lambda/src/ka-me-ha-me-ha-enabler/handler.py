import boto3
from botocore.exceptions import ClientError
import json
import os

class S3ObjectKeyNotSetError(Exception):
    def __init__(self, message):
        super().__init__(message)

class S3BucketNameNotSetError(Exception):
    def __init__(self, message):
        super().__init__(message)

class S3FileContentMissing(Exception):

    def __init__(self, message):
        super().__init__(message)


def dump_json_file(data: dict) -> bool:
    global bucket_name
    global object_key
    global s3_client

    s3_client.put_object(
        Bucket=bucket_name,
        Key=object_key,
        Body=json.dumps(data),
        ContentType="application/json"
    )


s3_client = boto3.client("s3")

bucket_name = os.getenv("BUCKET_NAME", None)

object_key = os.getenv("OBJECT_KEY", None)

if object_key is None:
    raise S3ObjectKeyNotSetError("Object Key for the file not set")

if bucket_name is None:
    raise S3BucketNameNotSetError("Bucket Name is not set in env")


def main(event, context):

    try:
        response = s3_client.get_object(
            Bucket = bucket_name,
            Key = object_key
        )

        raw_content = response['Body'].read().decode('utf-8')
        file_content = json.loads(raw_content)

    except ClientError as e:
        print(str(e))

        return {
            "statusCode": 500,
            "body": str(e)
        }

    if set(file_content.keys()) != {"previous", "current"}:
        raise S3FileContentMissing("File is empty / misconfigured")

    else:
        dump_json_file(
            data={
                "previous": file_content.get("current"),
                "current": event
            }
        )

    return {
        "statusCode": 200,
        "body": "Success :D"
    }

