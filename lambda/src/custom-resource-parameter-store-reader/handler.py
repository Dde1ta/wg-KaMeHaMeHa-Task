from typing import List
from cfnresponse import *
import boto3

def fetch_parameter(name: str, decrypt: bool, client) -> str | List[str] | None:
    response = client.get_parameter(
        Name=name,
        WithDecryption=decrypt
    )

    value = response['Parameter']['Value']

    return value


def main(event, context):
    """
        Properties:
          Region: "<aws-region>"
          Parameters:
            - <OutPutName>:
                Name: <Parameter Name>
                Decrypt: <True / False>
            - <OutPutName>:
                Name: <Parameter Name>
                Decrypt: <True / False>
            - <OutPutName>:
                Name: <Parameter Name>
                Decrypt: <True / False>


    :param event:
    :param context:
    :return:
    """
    print("getting valid Regions")

    try:

        properties = event.get('ResourceProperties', {})

        event_type = event.get('RequestType')

        print("Recived These propertiers", properties)

        if properties == {}:
            send(event=event,
                context=context,
                responseStatus=FAILED,
                responseData={},
                reason="Resource Properties are missing"
                )  # Send Failure :- Properties missing

            return {
                "statusCode": 500,
                "body": {
                    "message": "Failed: Resource Properties are missing"
                }
            }

        parameter_region = properties.get("Region", None)
        parameters = properties.get("Parameters", [{}])

        if parameter_region is None:
            send(
                event,
                context,
                responseStatus=FAILED,
                reason=f"Region cannot be empty"
            ) # Failure :- Region is Missing
            return {
                "statusCode": 400,
                "body": "Region is Missing"
            }

        if parameter_region == [{}]:
            send(
                event,
                context,
                responseStatus=FAILED,
                reason=f"Invaild / Unavailable Region {parameter_region}"
            )  # Invaild / Unavailable Region
            return {
                "statusCode": 400,
                "body": "Region is Invaild / Unavailable"
            }

        if parameters is None:
            send(
                event,
                context,
                responseStatus=FAILED,
                reason="Empty Parameter List"
            )  # Failure
            #Failure  # Failure :- Nothing to read

            return {
                "statusCode": 400,
                "body": "Parameter Are Missing"
            }

        response_data = {}

        client = boto3.client('ssm', region_name=parameter_region)

        try:
            if event_type == "Create" or event_type == "Update":
                print("Working")
                for param in parameters:
                    output_name = list(param.keys())[0]
                    param_name = param[output_name].get("Name")
                    param_decrypt = param[output_name].get("Decrypt", False).lower() == "true"

                    param_value = fetch_parameter(param_name, param_decrypt, client)

                    response_data[output_name] = param_value

            if event_type == "Delete":
                pass
            
            print("Work DOne")

        except Exception as e:
            send(
                event,
                context,
                responseStatus=FAILED,
                reason=str(e)
            )  #Failure

            return {
                "statusCode": 500,
                "body": "Bucket"
            }

        print("Cloudformation Status Sending")

        send(
            event,
            context,
            responseStatus=SUCCESS,
            responseData=response_data
        )

        print("Cloudformation Status Sent")

        return {
            "statusCode": 200,
            "body": "Bucket"
        }

    except Exception as e:
        send(
            event,
            context,
            responseStatus=FAILED,
            reason=str(e)
        )  #Failure

        return {
            "statusCode": 500,
            "body": "Bucket"
        }

    return {
        {
            "statusCode": 200,
            "body": "Bucket"
        }
    }