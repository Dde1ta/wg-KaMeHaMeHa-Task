import json

from ..resources.stacks import Stack
from ..resources.template import Templates
from ..exceptions.stack import *
from .config import *
from .bootstrap import *
import boto3

# actions


def initialize():
    print("Adding Replication Rule in us-west-2 bucket")

    s3_us_west_2.put_bucket_replication(
        Bucket=s3_stack_us_west_2.get_output().get("EncryptedS3BucketName"),
        ReplicationConfiguration={
            "Role": iam_stack.get_output().get("USWest2ToAPSouth1ReplicationRoleArn"),
            "Rules": [
                {
                    "Destination": {
                        "Bucket": f'arn:aws:s3:::{s3_stack_ap_south_1.get_output().get("EncryptedS3BucketName")}',
                        "EncryptionConfiguration": {
                            "ReplicaKmsKeyID": key_stack_ap_south_1.get_output().get("KMSReplicaKeyArn")
                        }
                    },
                    "Status": "Enabled",
                    "Filter": {
                        "Prefix": ""
                    },
                    "Priority": 1,
                    "DeleteMarkerReplication": {
                        "Status": "Disabled"
                    },
                    "SourceSelectionCriteria": {
                        "SseKmsEncryptedObjects": {
                            "Status": "Enabled"
                        }
                    }
                }
            ]
        }
    )

    print("Adding Replication Rule in ap-south-1 bucket")

    # arn:aws:s3:::ka-me-ha-me-ha-295345165437-us-west-2-an

    s3_ap_south_1.put_bucket_replication(
        Bucket=s3_stack_ap_south_1.get_output().get("EncryptedS3BucketName"),
        ReplicationConfiguration={
            "Role": iam_stack.get_output().get("APSouth1ToUSWest2ReplicationRoleArn"),
            "Rules": [
                {
                    "Destination": {
                        "Bucket": f'arn:aws:s3:::{s3_stack_us_west_2.get_output().get("EncryptedS3BucketName")}',
                        "EncryptionConfiguration": {
                            "ReplicaKmsKeyID": key_stack_us_west_2.get_output().get("KMSMainKeyArn")
                        }
                    },
                    "Status": "Enabled",
                    "Filter": {
                        "Prefix": ""
                    },
                    "Priority": 1,
                    "DeleteMarkerReplication": {
                        "Status": "Disabled"
                    },
                    "SourceSelectionCriteria": {
                        "SseKmsEncryptedObjects": {
                            "Status": "Enabled"
                        }
                    }
                }
            ]
        }
    )

    print(f"Adding empty {OBJECTIVE_FILE}")

    s3_us_west_2.put_object(
        Bucket=s3_stack_us_west_2.get_output().get("EncryptedS3BucketName"),
        Key=OBJECTIVE_FILE,
        Body=json.dumps(
            {
                "previous": {},
                "current": {}
            }
        )
    )


def deploy(stack: Stack,
           template_url: str | None = None,
           template_body: str | None = None,
           **parameters):
    try:
        stack_status = stack.get_stack_status()

        if stack_status == "CREATE_COMPLETE" or stack_status == "UPDATE_COMPLETE":
            print("Stack Exists")

            if template_body:
                stack.set_and_validate_template(template_body=template_body)
            elif template_url:
                stack.set_and_validate_template(template_url=template_url)
            else:
                raise ValueError("Either Template url or Template body is required")

            for params in parameters:

                stack.set_parameters(
                    parameter_key=params,
                    parameter_value=parameters.get(params, "Not Set")
                )

            print("Stack Exists Creating Change Set")
            stack.create_drift_aware_change_set()

            print("Waiting for it")
            stack.wait_for_change_set_creation()

            print("Executing Change Set")
            stack.execute_change_set()

            print("Waiting for it")
            stack.wait_for_update()

            return

    except StackDoesNotExist as e:
        print(f"Making {stack.name} as it is not found")

        if template_body:
            stack.set_and_validate_template(template_body=template_body)
        elif template_url:
            stack.set_and_validate_template(template_url=template_url)
        else:
            raise ValueError("Either Template url or Template body is required")

        for key, value in parameters.items():
            stack.set_parameters(parameter_key=key, parameter_value=value)

        stack.start_stack_creation()
        stack.wait_for_creation()

        print(f"Stack {stack.name} is created")

    except StackNotChanged:
        print(f"Stack {stack.name} is unchanged")
        return

    except TemplateValidationFailed as e:
        print("TemplateValidationFailed")
        print(e)

    except StackException as e:
        print(e.reason)


# sessions
us_west_2_session = boto3.Session(region_name="us-west-2", profile_name="test-chahal")
ap_south_1_session = boto3.Session(region_name="ap-south-1", profile_name="test-chahal")

# clients
cfn_us_west_2 = us_west_2_session.client("cloudformation")
cfn_ap_south_1 = ap_south_1_session.client("cloudformation")

s3_ap_south_1 = ap_south_1_session.client("s3")
s3_us_west_2 = us_west_2_session.client("s3")

# account_id
sts_client = boto3.client('sts')
account = sts_client.get_caller_identity()['Account']

del sts_client

# Stacks

bootstrap_stack_us_west_2 = Stack(cfn_client=cfn_us_west_2,
                                  stack_name=BOOTSTRAP_STACK_NAME)

bootstrap_stack_ap_south_1 = Stack(cfn_client=cfn_ap_south_1,
                                   stack_name=BOOTSTRAP_STACK_NAME)

iam_stack = Stack(
    cfn_client=cfn_us_west_2,
    stack_name=IAM_STACK_NAME
)

key_stack_us_west_2 = Stack(
    cfn_client=cfn_us_west_2,
    stack_name=KMS_MAIN_STACK_NAME
)

dynamodb_stack_us_west_2 = Stack(
    cfn_client=cfn_us_west_2,
    stack_name=DYNAMODB_STACK_NAME
)

lambda_stack_us_west_2 = Stack(
    cfn_client=cfn_us_west_2,
    stack_name=LAMBDA_STACK_NAME
)

s3_stack_us_west_2 = Stack(
    cfn_client=cfn_us_west_2,
    stack_name=S3_STACK_NAME
)

key_stack_ap_south_1 = Stack(
    cfn_client=cfn_ap_south_1,
    stack_name=KMS_REPLICA_STACK_NAME
)

s3_stack_ap_south_1 = Stack(
    cfn_client=cfn_ap_south_1,
    stack_name=S3_STACK_NAME
)


# Templates

templates_us_west_2 = Templates(s3_us_west_2)

templates_ap_south_1 = Templates(s3_ap_south_1)

# Start deployments :D


print("Readying us-west-2")

boot_strap_main(bootstrap_stack_us_west_2, US_WEST_2_TEMPLATE_PATHS)
bootstrap_stack_us_west_2_outputs = bootstrap_stack_us_west_2.get_output()
templates_us_west_2.set_template_bucket(bootstrap_stack_us_west_2_outputs.get("S3BucketName", "Error"))
upload_templates(templates_us_west_2, US_WEST_2_TEMPLATE_PATHS)

print("uploading Zips")
templates_us_west_2.upload_lambda_zips(*list(CODE_ZIPS_PATH.values()))

print("Readying ap-south-1")

boot_strap_main(bootstrap_stack_ap_south_1, AP_SOUTH_1_TEMPLATE_PATHS)
bootstrap_stack_ap_south_1_outputs = bootstrap_stack_ap_south_1.get_output()
templates_ap_south_1.set_template_bucket(bootstrap_stack_ap_south_1_outputs.get("S3BucketName", "Error"))
upload_templates(templates_ap_south_1, AP_SOUTH_1_TEMPLATE_PATHS)

print("Deploying Keys")

print("us-west-2")

# print(templates_us_west_2.templates)

deploy(
    stack=key_stack_us_west_2,
    template_url=templates_us_west_2.get_template_url(US_WEST_2_TEMPLATE_PATHS[KMS_MAIN_STACK_NAME]),
    CreateReplicaKey="False",
    CreateKeys="True"
)

print("ap-south-1")

deploy(
    stack=key_stack_ap_south_1,
    template_url=templates_ap_south_1.get_template_url(AP_SOUTH_1_TEMPLATE_PATHS[KMS_REPLICA_STACK_NAME]),
    CreateReplicaKey="True",
    CreateKeys="True",
    KMSMainKeyArn=key_stack_us_west_2.get_output().get("KMSMainKeyArn")
)

print("Deploying IAM ROLES")

deploy(
    stack=iam_stack,
    template_url=templates_us_west_2.get_template_url(US_WEST_2_TEMPLATE_PATHS[IAM_STACK_NAME]),
    USWest2BucketName=S3_BUCKET_NAME,
    APSouth1BucketName=S3_BUCKET_NAME,
    USWest2KMSKeyArn=key_stack_us_west_2.get_output().get("KMSMainKeyArn"),
    APSouth1KMSKeyArn=key_stack_ap_south_1.get_output().get("KMSReplicaKeyArn")
)

print("Deploying Dynamodb")

deploy(
    stack=dynamodb_stack_us_west_2,
    template_url=templates_us_west_2.get_template_url(US_WEST_2_TEMPLATE_PATHS[DYNAMODB_STACK_NAME]),
)

print("Deploying us-west-2 bucket")

deploy(
    stack=s3_stack_us_west_2,
    template_url=templates_us_west_2.get_template_url(US_WEST_2_TEMPLATE_PATHS[S3_STACK_NAME]),
    SSEKMSKeyID=key_stack_us_west_2.get_output().get("KMSMainKeyArn")
)


print("Deploying Lambda")

deploy(
    stack=lambda_stack_us_west_2,
    template_url=templates_us_west_2.get_template_url(US_WEST_2_TEMPLATE_PATHS[LAMBDA_STACK_NAME]),
    EnablerLambdaFunctionExecutionRoleArn=iam_stack.get_output().get("EnablerLambdaFunctionExecutionRoleArn"),
    EnablerLambdaFunctionCodeBucket=bootstrap_stack_us_west_2.get_output().get("S3BucketName"),
    EnablerLambdaFunctionCodeZipObjectKey=CODE_ZIPS_PATH[LAMBDA_STACK_NAME],
    EnablerLambdaFunctionEnvBucketName=s3_stack_us_west_2.get_output().get("EncryptedS3BucketName"),
    EnablerLambdaFunctionEnvObjectKey=OBJECTIVE_FILE,
    DynamodbStreamArn=dynamodb_stack_us_west_2.get_output().get("DynamoDBTableStreamArn"),
)

print("Deploying ap-south-1 bucket")

deploy(
    stack=s3_stack_ap_south_1,
    template_url=templates_ap_south_1.get_template_url(AP_SOUTH_1_TEMPLATE_PATHS[S3_STACK_NAME]),
    SSEKMSKeyID=key_stack_ap_south_1.get_output().get("KMSReplicaKeyArn")
)

print("Initializing resources")

initialize()
