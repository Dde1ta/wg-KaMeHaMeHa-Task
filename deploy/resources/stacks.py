from typing import List, Callable
from ..exceptions.stack import *
from botocore.exceptions import ClientError, WaiterError
import boto3
import uuid


class Stack:

    def __init__(self, cfn_client, stack_name: str):
        self.client = cfn_client
        self.name = stack_name
        self.region = cfn_client.meta.region_name

        self.template_body = None
        self.capabilities = []
        self.parameters = {}
        self.template_url = None
        self.outputs = None

    def get_stack_status(self) -> str:
        """
        Returns stacks progress.
        :return: Stack status e.g. CREATE_COMPLETE, CREATE_IN_PROGRESS
        """

        try:

            response = self.client.describe_stacks(
                StackName=self.name
            )

            stack_status = response["Stacks"][0].get("StackStatus")

            return stack_status

        except ClientError as e:
            error = e.response.get("Error")

            if error.get("Code") == "ValidationError":
                raise StackDoesNotExist(f"Stack {self.name} not found in region {self.region}")

            else:
                raise StackException("An error occurred during stack status check", reason=error)

    def __formated_parameters(self) -> list:
        return_dict = []

        for param in self.parameters:
            return_dict.append(
                {
                    "ParameterKey": param,
                    "ParameterValue": self.parameters[param]
                }
            )

        return return_dict

    def set_and_validate_template(self, template_url: str = None, template_body: str = None) -> None:
        try:

            if template_body is None:

                response = self.client.validate_template(
                    TemplateURL=template_url
                )

                self.template_url = template_url

            else:
                response = self.client.validate_template(
                    TemplateBody=template_body
                )

                self.template_body = template_body

            parameters = response.get("Parameters", [])
            self.capabilities = response.get("Capabilities", [])

            self.parameters = {}

            for parameter in parameters:
                self.parameters[parameter["ParameterKey"]] = parameter.get("DefaultValue", None)

        except ClientError as e:

            error = e.response.get("Error")

            if "Template format error" in error.get("Message"):
                raise TemplateValidationFailed(message=error.get("Message"))

            else:
                raise StackException("Error in validating template", reason=e.response)

    def set_parameters(self, parameter_key: str, parameter_value: str):

        if parameter_key not in self.parameters.keys():
            raise InvalidParameter(f"{parameter_key} is not a parameter in the template")

        self.parameters[parameter_key] = parameter_value

    def get_output(self) -> dict:

        response = self.client.describe_stacks(
            StackName=self.name
        )

        stack_details = response["Stacks"][0]

        output_list = stack_details.get("Outputs", [])
        self.outputs = {out["OutputKey"]: out["OutputValue"] for out in output_list}
        return self.outputs

    def start_stack_creation(self) -> str:
        try:

            if (self.template_url is None
                    and
                    self.template_body is None):
                raise StackNotInitialized(message=f"Stack not ready set template run get_template")

            if self.template_body is None:

                response = self.client.create_stack(
                    StackName=self.name,
                    TemplateURL=self.template_url,
                    Parameters=self.__formated_parameters(),
                    Capabilities=self.capabilities
                )

            else:

                response = self.client.create_stack(
                    StackName=self.name,
                    TemplateBody=self.template_body,
                    Parameters=self.__formated_parameters(),
                    Capabilities=self.capabilities
                )

            self.stack_id = response["StackId"]
            self.operation_id = response["OperationId"]

            return self.stack_id

        except self.client.exceptions.AlreadyExistsException as e:
            raise StackAlreadyExist(f"Stack {self.name} already exists")

        except ClientError as e:
            raise StackException(f"Stack Creation Not Started", reason=e.response)

    def wait_for_creation(self):
        waiter = self.client.get_waiter('stack_create_complete')

        try:

            waiter.wait(
                StackName=self.name,
                WaiterConfig={
                    'Delay': 30,
                    'MaxAttempts': 40
                }
            )

        except WaiterError as e:
            raise StackException(f"Waiter Failed for Stack {self.name}", reason=e.last_response)

    def create_drift_aware_change_set(self):
        try:
            if (self.template_url is None
                    and
                    self.template_body is None):
                raise StackNotInitialized(message=f"Stack not ready set template run get_template")

            change_set_name = f"{self.name}-{uuid.uuid4()}"

            print(f"Creating Change Set {change_set_name}")

            if self.template_body is None:
                response = self.client.create_change_set(
                    StackName=self.name,
                    TemplateURL=self.template_url,
                    Parameters=self.__formated_parameters(),
                    Capabilities=self.capabilities,
                    ChangeSetName=change_set_name,
                    DeploymentMode="REVERT_DRIFT",
                    ChangeSetType="UPDATE"
                )
            else:
                response = self.client.create_change_set(
                    StackName=self.name,
                    TemplateBody=self.template_body,
                    Parameters=self.__formated_parameters(),
                    Capabilities=self.capabilities,
                    ChangeSetName=change_set_name,
                    DeploymentMode="REVERT_DRIFT",
                    ChangeSetType="UPDATE"
                )

            self.change_set_id = response.get("Id")
            self.change_set_name = change_set_name

        except ClientError as e:
            raise StackException("Stack Update could not start", reason=e.response)

    def wait_for_change_set_creation(self):
        waiter = self.client.get_waiter('change_set_create_complete')

        try:

            waiter.wait(
                ChangeSetName=self.change_set_name,
                StackName=self.name,
                WaiterConfig={
                    'Delay': 5,
                    'MaxAttempts': 500
                }
            )

        except WaiterError as e:

            status_reason = e.last_response.get("StatusReason", "")

            if "didn't contain changes" in status_reason or "No updates are to be performed" in status_reason:
                raise StackNotChanged(f"No changes detected for stack {self.name}.")
            else:
                raise StackException(f"Change set creation failed for {self.name}", reason=status_reason)

    def execute_change_set(self):
        try:
            if not hasattr(self, 'change_set_name') or self.change_set_name is None:
                raise StackNotInitialized(message="Change set not created for execution")

            self.client.execute_change_set(
                ChangeSetName=self.change_set_name,
                StackName=self.name
            )

        except ClientError as e:
            raise StackException("Failed to execute change set", reason=e.response)

    def wait_for_update(self):
        waiter = self.client.get_waiter('stack_update_complete')

        try:
            waiter.wait(
                StackName=self.name,
                WaiterConfig={
                    'Delay': 5,
                    'MaxAttempts': 500
                }
            )

        except WaiterError as e:
            raise StackException(f"Waiter Failed for Stack Update {self.name}", reason=e.last_response)

# if __name__ == "__main__":
#     sts_client = boto3.client('sts')
#     account_id = sts_client.get_caller_identity()['Account']
#
#     del sts_client
#
#     region = "ap-south-1"
#
#     cfn = boto3.client("cloudformation", region_name=region)
#
#     test = Stack(cfn_client= cfn, stack_name="test-not-made-yet")
#
#     test.set_and_validate_template(
#         template_url="https://my-indian-cloudformation-templates-295345165437-ap-south-1-an.s3.amazonaws.com\
#         /KaMeHaMeHa/Main/templates/ap-south-1-resources/KMS-Replica-Key.yaml"
#     )
#
#
