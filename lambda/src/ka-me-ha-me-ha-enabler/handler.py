import boto3
from botocore.exceptions import ClientError
import json
import os
from item import Item


class S3FileContentMissing(Exception):

    def __init__(self, message):
        super().__init__(message)


def dump_json_file(data: dict) -> dict[str, int | str]:
    global bucket_name
    global object_key
    global s3_client

    try:
        s3_client.put_object(
            Bucket=bucket_name,
            Key=object_key,
            Body=json.dumps(data),
            ContentType="application/json"
        )

        return {
            "statusCode": 200,
            "body": "Success :D"
        }

    except Exception as e:
        print(e)
        return {
            "statusCode": 500,
            "body": str(e)
        }


s3_client = boto3.client("s3")

bucket_name = os.getenv("BUCKET_NAME", None)

object_key = os.getenv("OBJECT_KEY", None)


def main(event: dict, context):

    try:
        response = s3_client.get_object(
            Bucket=bucket_name,
            Key=object_key
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
        current_object = {"Items": []}
        for record in event.get("Records"):
            try:
                new_item = Item()

                record = record["dynamodb"].get("NewImage")

                sort_key = record["DefenderTimestamp"].get("S")
                defender = "#".join(sort_key.split("#")[:2])
                timestamp = sort_key.split("#")[-1]

                new_item.attacker = record["Attacker"].get("S")
                new_item.defender = defender
                new_item.result = record["Success"].get("BOOL", False)
                new_item.timestamp = timestamp
                new_item.location = record["Location"].get("S", "Unknown")
                new_item.reason = record["Reason"].get("S", "Unknown")
                new_item.damage = record["Damage"].get("N", 0)

                current_object["Items"].append(new_item.to_dict())

            except ValueError as e:
                print(e)
                print(record)

                current_object["Items"].append(
                    {
                        "Error": str(e),
                        "Status": "The item processing failed"
                    }
                )

        return dump_json_file(
            {
                "previous": file_content.get("current"),
                "current": current_object
            }
        )
