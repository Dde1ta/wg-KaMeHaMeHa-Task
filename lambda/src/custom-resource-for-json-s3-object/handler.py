import boto3
from cfnresponse import *
import json

s3_client = boto3.client('s3')

def main(event, context):
    """
        Properties:
          BucketName: String
          S3ObjectKey: String
          JSONKeys:
            - String 
    """
    properties = event.get('ResourceProperties', {})

    if properties == {}:
        send(event=event,
            context=context,
            responseStatus=FAILED,
            responseData = {},
            reason="Resource Properties are missing"
        )  # Send Failure :- Properties missing

        return {
            "statusCode": 500,
            "body": {
                "message": "Failed: Resource Properties are missing"
            }
        }

    bucket_name = properties.get('BucketName', None)
    object_key = properties.get("S3ObjectKey", None)
    file_content = properties.get("JSONKeys", None)
    event_type = event.get('RequestType')


    if bucket_name is None:
        send(event=event,
            context=context,
            responseStatus=FAILED,
            responseData={},
            reason="BucketName Property are missing"
        )  # Send Failure :- Properties missing

        return {
            "statusCode": 500,
            "body": {
                "message": "Failed: BucketName Property missing"
            }
        }

    if object_key is None:
        send(event=event,
            context=context,
            responseStatus=FAILED,
            responseData={},
            reason="S3ObjectKey Property are missing"
        )  # Send Failure :- Properties missing

        return {
            "statusCode": 500,
            "body": {
                "message": "Failed: S3ObjectKey Property missing"
            }
        }

    if file_content is None:
        send(event=event,
            context=context,
            responseStatus=FAILED,
            responseData={},
            reason="JSONKeys Property are missing"
        )  # Send Failure :- Properties missing

        return {
            "statusCode": 500,
            "body": {
                "message": "Failed: JSONKeys Property missing"
            }
        }


    try :
        if event_type == "Create":
            initial_dict = {i:{} for i in file_content}

            response = s3_client.put_object(
                Bucket=bucket_name,
                Key=object_key,
                Body=json.dumps(initial_dict),
                ContentType="application/json"
            )

            versionId = response.get("VersionId")

            send(event=event,
                context=context,
                responseStatus=SUCCESS,
                responseData={
                    "versionId": versionId
                },
                reason=f"Created Initial File with content {initial_dict}"
            )  # Success

        if event_type == "Update":
            send(event=event,
                context=context,
                responseStatus=SUCCESS,
                responseData={},
                reason=f"Not Updating file, can reset and clear file"
            )  # Success

        if event_type == "Delete":
            s3_client.delete_object(
                Bucket=bucket_name,
                Key=object_key
            )

    except Exception as e:
        send(event=event,
            context=context,
            responseStatus=FAILED,
            responseData={},
            reason=f"Error In creating File: {str(e)}"
        )  # Failure

    return {
        "statusCode": 200,
        "body": {
            "message": "Success :D"
        }
    }