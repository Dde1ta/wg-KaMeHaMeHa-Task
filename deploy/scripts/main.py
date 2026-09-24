import json
import boto3

from ..resources.stacks import Stack
from ..resources.template import Templates
from ..exceptions.stack import *
from .config import *
import sys


# actions

def upload_templates(templates: Templates, paths: dict):
    print("Uploading Templates one - by - one")

    templates.upload_templates(*list(paths.values()))


def initialize():
    if skip_initialize:
        print("Skipping initialization !!")
        return

    us_west_2_bucket = s3_stack_us_west_2.get_output().get("EncryptedS3BucketName")
    ap_south_1_bucket = s3_stack_ap_south_1.get_output().get("EncryptedS3BucketName")

    print(f"Configuring S3 Cross-Region Replication: {us_west_2_bucket} (us-west-2) -> {ap_south_1_bucket} (ap-south-1)")
    s3_us_west_2.put_bucket_replication(
        Bucket=us_west_2_bucket,
        ReplicationConfiguration={
            "Role": iam_stack.get_output().get("PrimaryToSecondaryReplicationRoleArn"),
            "Rules": [
                {
                    "Destination": {
                        "Bucket": f'arn:aws:s3:::{ap_south_1_bucket}',
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
                        "Status": "Enabled"
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

    print(
        f"Configuring S3 Cross-Region Replication: {ap_south_1_bucket} (ap-south-1) -> {us_west_2_bucket} (us-west-2)")
    s3_ap_south_1.put_bucket_replication(
        Bucket=ap_south_1_bucket,
        ReplicationConfiguration={
            "Role": iam_stack.get_output().get("SecondaryToPrimaryReplicationRoleArn"),
            "Rules": [
                {
                    "Destination": {
                        "Bucket": f'arn:aws:s3:::{us_west_2_bucket}',
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
                        "Status": "Enabled"
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

    print(f"Uploading initial state file '{OBJECTIVE_FILE}' to bucket {us_west_2_bucket}")
    s3_us_west_2.put_object(
        Bucket=us_west_2_bucket,
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
           **parameters) -> None:
    try:
        stack_status = stack.get_stack_status()

        print(f"[{stack.name}] Stack exists.")

        if stack_status in ["CREATE_COMPLETE", "UPDATE_COMPLETE"]:
            if skip_updates:
                print("Skipping Update.....")
                return

            print(f" Validating template...")

            if template_body:
                stack.set_and_validate_template(template_body=template_body)
            elif template_url:
                stack.set_and_validate_template(template_url=template_url)
            else:
                raise ValueError(f"[{stack.name}] Deployment failed: Either template_url or template_body is required.")

            for key, value in parameters.items():
                print(f"Debug: {stack.name} -> Setting param {key} = {value}")
                stack.set_parameters(parameter_key=key, parameter_value=value)

            print(f"[{stack.name}] Generating change set for updates...")
            stack.create_drift_aware_change_set()

            print(f"[{stack.name}] Waiting for change set creation to finish...")
            stack.wait_for_change_set_creation()

            print(f"[{stack.name}] Executing change set...")
            stack.execute_change_set()

            print(f"[{stack.name}] Waiting for stack update to complete...")
            stack.wait_for_update()
            print(f"[{stack.name}] Stack update completed successfully.")

            return

        raise UnHandleableStackState(
            f"Stack {stack.name} in {stack_status} which this script cannot handle",
            reason=stack.get_stack_status_reason()
        )

    except StackDoesNotExist as e:
        print(f"[{stack.name}] Stack not found. Initiating creation sequence...")

        if template_body:
            stack.set_and_validate_template(template_body=template_body)
        elif template_url:
            stack.set_and_validate_template(template_url=template_url)
        else:
            raise ValueError(f"[{stack.name}] Deployment failed: Either template_url or template_body is required.")

        for key, value in parameters.items():
            print(f"Debug: {stack.name} -> Setting param {key} = {value}")
            stack.set_parameters(parameter_key=key, parameter_value=value)

        stack.start_stack_creation()

        print(f"[{stack.name}] Waiting for stack creation to complete...")
        stack.wait_for_creation()
        print(f"[{stack.name}] Stack created successfully.")

    except StackNotChanged:
        print(f"[{stack.name}] No changes detected. Skipping update.")
        return

    except TemplateValidationFailed as e:
        print(f"[{stack.name}] Template validation failed: {e}")

    except StackException as e:
        print(f"[{stack.name}] Stack operation failed: {e.reason}")


def start_deployments():
    # Start deployments :D

    print("\n--- Bootstrapping us-west-2 ---")

    with open(US_WEST_2_TEMPLATE_PATHS[BOOTSTRAP_STACK_NAME], "r") as file:
        deploy(
            stack=bootstrap_stack_us_west_2,
            template_body=file.read(),
            BucketName=TEMPLATE_BUCKET_NAME
        )

    bootstrap_stack_us_west_2_outputs = bootstrap_stack_us_west_2.get_output()
    templates_us_west_2.set_template_bucket(bootstrap_stack_us_west_2_outputs.get("S3BucketName", "Error"))
    upload_templates(templates_us_west_2, US_WEST_2_TEMPLATE_PATHS)

    print("Uploading Lambda deployment ZIP packages to us-west-2...")
    templates_us_west_2.upload_lambda_zips(*list(CODE_ZIPS_PATH.values()))

    print("\n--- Bootstrapping ap-south-1 ---")
    with open(AP_SOUTH_1_TEMPLATE_PATHS[BOOTSTRAP_STACK_NAME], "r") as file:
        deploy(
            stack=bootstrap_stack_ap_south_1,
            template_body=file.read(),
            BucketName=TEMPLATE_BUCKET_NAME
        )
    bootstrap_stack_ap_south_1_outputs = bootstrap_stack_ap_south_1.get_output()
    templates_ap_south_1.set_template_bucket(bootstrap_stack_ap_south_1_outputs.get("S3BucketName", "Error"))
    upload_templates(templates_ap_south_1, AP_SOUTH_1_TEMPLATE_PATHS)

    print("\n--- Deploying KMS Keys ---")
    print("Deploying Primary Multi-Region KMS Key (us-west-2)...")
    deploy(
        stack=key_stack_us_west_2,
        template_url=templates_us_west_2.get_template_url(US_WEST_2_TEMPLATE_PATHS[KMS_MAIN_STACK_NAME]),
        CreateReplicaKey="False"
    )

    print("Deploying Replica KMS Key (ap-south-1)...")
    deploy(
        stack=key_stack_ap_south_1,
        template_url=templates_ap_south_1.get_template_url(AP_SOUTH_1_TEMPLATE_PATHS[KMS_REPLICA_STACK_NAME]),
        CreateReplicaKey="True",
        KMSMainKeyArn=key_stack_us_west_2.get_output().get("KMSMainKeyArn")
    )

    print("\n--- Deploying Table ---")
    print("Deploying DynamoDB State Table (us-west-2)...")
    deploy(
        stack=dynamodb_stack_us_west_2,
        template_url=templates_us_west_2.get_template_url(US_WEST_2_TEMPLATE_PATHS[DYNAMODB_STACK_NAME]),
        DynamodbTableName="ka-me-ha-me-ha-archives"
    )

    print("\n--- Deploying Buckets  ---")
    print("Deploying Encrypted S3 Bucket (us-west-2)...")
    deploy(
        stack=s3_stack_us_west_2,
        template_url=templates_us_west_2.get_template_url(US_WEST_2_TEMPLATE_PATHS[S3_STACK_NAME]),
        SSEKMSKeyID=key_stack_us_west_2.get_output().get("KMSMainKeyArn"),
        BucketName="ka-me-ha-me-ha"
    )

    print("Deploying Encrypted S3 Bucket (ap-south-1)...")
    deploy(
        stack=s3_stack_ap_south_1,
        template_url=templates_ap_south_1.get_template_url(AP_SOUTH_1_TEMPLATE_PATHS[S3_STACK_NAME]),
        SSEKMSKeyID=key_stack_ap_south_1.get_output().get("KMSReplicaKeyArn"),
        BucketName="ka-me-ha-me-ha"
    )

    print("\n--- Deploying IAM Roles ---")
    print("Deploying S3 Replication and Lambda Execution Roles...")
    deploy(
        stack=iam_stack,
        template_url=templates_us_west_2.get_template_url(US_WEST_2_TEMPLATE_PATHS[IAM_STACK_NAME]),
        PrimaryBucketArn=s3_stack_us_west_2.get_output().get("EncryptedS3BucketArn"),
        SecondaryBucketArn=s3_stack_ap_south_1.get_output().get("EncryptedS3BucketArn"),
        PrimaryKMSKeyArn=key_stack_us_west_2.get_output().get("KMSMainKeyArn"),
        SecondaryKMSKeyArn=key_stack_ap_south_1.get_output().get("KMSReplicaKeyArn")
    )

    print("\n--- Deploying Lambda Function ---")
    print("Deploying Event-Driven Lambda Function (us-west-2)...")
    deploy(
        stack=lambda_stack_us_west_2,
        template_url=templates_us_west_2.get_template_url(US_WEST_2_TEMPLATE_PATHS[LAMBDA_STACK_NAME]),
        ExecutionRoleArn=iam_stack.get_output().get("EnablerLambdaFunctionExecutionRoleArn"),
        ExecutionRoleName=iam_stack.get_output().get("EnablerLambdaFunctionExecutionRoleName"),
        CodeBucket=bootstrap_stack_us_west_2.get_output().get("S3BucketName"),
        CodeZipObjectKey=CODE_ZIPS_PATH[LAMBDA_STACK_NAME],
        BucketNameEnv=s3_stack_us_west_2.get_output().get("EncryptedS3BucketName"),
        ObjectKeyEnv=OBJECTIVE_FILE,
        DynamodbStreamArn=dynamodb_stack_us_west_2.get_output().get("DynamoDBTableStreamArn"),
        KMSKeyArn=key_stack_us_west_2.get_output().get("KMSMainKeyArn"),
        LambdaFunctionName="ka-me-ha-me-ha--enabler"
    )

    print("\n--- Finalizing Post-Deployment Configuration ---")
    initialize()
    print("\nDeployment pipeline completed successfully.")


if __name__ == "__main__":
    skip_updates = False
    skip_initialize = True
    profile = "default"

    if len(sys.argv) > 1 and "--skip-updates" in sys.argv:
        try:
            skip_updates = sys.argv[sys.argv.index("--skip-updates") + 1].lower() == "true"
        except IndexError:
            pass

    if len(sys.argv) > 1 and "--skip-initialize" in sys.argv:
        try:
            skip_initialize = sys.argv[sys.argv.index("--skip-initialize") + 1].lower() == "true"
        except IndexError:
            pass

    if len(sys.argv) > 1 and "--profile" in sys.argv:
        try:
            profile = sys.argv[sys.argv.index("--profile") + 1]
        except IndexError:
            pass

    print("Info: Skipping Updates set to -> ", skip_updates)
    print("Info: Skipping Initialize set to ->", skip_initialize)
    print("Info: Set Profile to ->", profile)

    # sessions
    us_west_2_session = boto3.Session(region_name="us-west-2", profile_name=profile)
    ap_south_1_session = boto3.Session(region_name="ap-south-1", profile_name=profile)

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
    bootstrap_stack_us_west_2  = Stack(cfn_client=cfn_us_west_2, stack_name=BOOTSTRAP_STACK_NAME)
    bootstrap_stack_ap_south_1 = Stack(cfn_client=cfn_ap_south_1, stack_name=BOOTSTRAP_STACK_NAME)
    iam_stack                  = Stack(cfn_client=cfn_us_west_2, stack_name=IAM_STACK_NAME)
    key_stack_us_west_2        = Stack(cfn_client=cfn_us_west_2, stack_name=KMS_MAIN_STACK_NAME)
    dynamodb_stack_us_west_2   = Stack(cfn_client=cfn_us_west_2, stack_name=DYNAMODB_STACK_NAME)
    lambda_stack_us_west_2     = Stack(cfn_client=cfn_us_west_2, stack_name=LAMBDA_STACK_NAME)
    s3_stack_us_west_2         = Stack(cfn_client=cfn_us_west_2, stack_name=S3_STACK_NAME)
    key_stack_ap_south_1       = Stack(cfn_client=cfn_ap_south_1, stack_name=KMS_REPLICA_STACK_NAME)
    s3_stack_ap_south_1        = Stack(cfn_client=cfn_ap_south_1, stack_name=S3_STACK_NAME)

    # Templates
    templates_us_west_2        = Templates(s3_us_west_2)
    templates_ap_south_1       = Templates(s3_ap_south_1)

    start_deployments()
