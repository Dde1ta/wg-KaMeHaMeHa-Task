import boto3
from cfnresponse import *

s3_client = boto3.client('s3')

def type_correct_configuration(replication_configuration, event, context):
    print(replication_configuration)

    # CloudFormation 'Rules' is a list
    rules = replication_configuration.get("Rules", [])

    if len(rules) == 0:
        send(
            event=event,
            context=context,
            responseStatus=FAILED,
            reason="ReplicationConfiguration Rules Missing"
        )
        return None # Return None to signal a failure to main()

    try:
        # Iterate over the list of rules
        for rule in rules:
            if "Priority" in rule:
                rule["Priority"] = int(rule["Priority"])
                
        replication_configuration["Rules"] = rules
        return replication_configuration
        
    except ValueError as e:
        send(
            event=event,
            context=context,
            responseStatus=FAILED,
            reason="Priority Rule Should be a number"
        )
        return None # Return None to signal a failure to main()

def main(event, context):
    properties = event.get('ResourceProperties', {})
    bucket_name = properties.get('BucketName')
    bucket_replica_configuration = properties.get('ReplicationConfiguration', {})
    event_type = event.get('RequestType')

    bucket_replica_configuration = type_correct_configuration(bucket_replica_configuration, event, context)

    if bucket_replica_configuration is None:
        return {
            "statusCode": 500,
            "body": "Validation failed in type_correct_configuration"
        }

    if not bucket_replica_configuration:
        send(
            event=event,
            context=context,
            responseStatus=FAILED,
            reason="Bucket ReplicationConfiguration is a Required Property"
        )
        return {
            "statusCode": 500,
            "body": "ReplicationConfiguration missing from resource"
        }

    if bucket_name is None:
        send(
            event=event,
            context=context,
            responseStatus=FAILED,
            reason="Bucket Name is a Required Property"
        )
        return {
            "statusCode": 500,
            "body": "Name missing from resource"
        }

    try:
        if event_type == "Create":
            s3_client.put_bucket_replication(
                Bucket=bucket_name,
                ReplicationConfiguration=bucket_replica_configuration
            )

        if event_type == "Delete":
            s3_client.delete_bucket_replication(
                Bucket=bucket_name
            ) 

        if event_type == "Update":                
            s3_client.delete_bucket_replication(
                Bucket=bucket_name
            ) 
            s3_client.put_bucket_replication(
                Bucket=bucket_name,
                ReplicationConfiguration=bucket_replica_configuration
            )
            
    except Exception as e:
        send(
            event=event,
            context=context,
            responseStatus=FAILED,
            reason=str(e)
        )
        return {
            "statusCode": 500,
            "body": str(e)
        }

    send(
        event=event,
        context=context,
        responseStatus=SUCCESS,
        reason=f"Successfully processed Replication rule for bucket {bucket_name}"
    )

    return {
        "statusCode": 200,
        "body": f"Successfully processed Replication rule for bucket {bucket_name}"
    }