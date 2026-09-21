from ..resources.stacks import Stack
from ..resources.template import Templates
from ..exceptions.stack import *
from .config import *
import boto3

"""
Set of functions in the bootstrap process
"""


def upload_templates(templates: Templates, paths: dict):
    print("Uploading Templates one - by - one")

    templates.upload_templates(*list(paths.values()))


def boot_strap_main(bootstrap_stack: Stack, paths: dict):

    try:
        stack_status = bootstrap_stack.get_stack_status()

        if stack_status == "CREATE_COMPLETE" or stack_status == "UPDATE_COMPLETE":
            print("Stack Exists")

            with open(paths[BOOTSTRAP_STACK_NAME], "r") as file:
                bootstrap_stack.set_and_validate_template(template_body=file.read())
                bootstrap_stack.set_parameters(
                    parameter_key="BucketName",
                    parameter_value=TEMPLATE_BUCKET_NAME
                )

            print("Stack Exists Creating Change Set")
            bootstrap_stack.create_drift_aware_change_set()

            print("Waiting for it")
            bootstrap_stack.wait_for_change_set_creation()

            print("Executing Change Set")
            bootstrap_stack.execute_change_set()

            print("Waiting for it")
            bootstrap_stack.wait_for_update()

            print("Bucket Ready for templates")

            return

    except StackDoesNotExist as e:
        print(f"Making {BOOTSTRAP_STACK_NAME} as it is not found")
        with open(paths[BOOTSTRAP_STACK_NAME], "r") as file:
            bootstrap_stack.set_and_validate_template(template_body=file.read())
            bootstrap_stack.set_parameters(
                parameter_key="BucketName",
                parameter_value=TEMPLATE_BUCKET_NAME
            )

            bootstrap_stack.start_stack_creation()
            bootstrap_stack.wait_for_creation()

        print("Made The Stack and is ready for templates")

    except StackNotChanged:
        print("Bucket Ready for templates")
        return

    except TemplateValidationFailed as e:
        print("TemplateValidationFailed")
        print(e)

    except StackException as e:
        print(e.reason)


# if __name__ == "__main__":
#     sts_client = boto3.client('sts')
#     account = sts_client.get_caller_identity()['Account']
#
#     del sts_client
#
#     region = "ap-south-1"
#
#     cfn = boto3.client("cloudformation", region_name=region)
#     s3 = boto3.client("s3", region_name=region)
#
#     bootstrap_stack = Stack(cfn_client=cfn,
#                             stack_name=BOOTSTRAP_STACK_NAME)
#
#     boot_strap_main(bootstrap_stack)
#
#     outputs = bootstrap_stack.get_output()
#
#     print(outputs)
#
#     templates = Templates(
#         s3_client=s3,
#         bucket_name=outputs.get("S3BucketName", "ErrorTHIS")
#     )
#
#     upload_templates(templates)
