"""
I Do not need this -> just keep it like this for now.
"""

import boto3
from cfnresponse import *
from typing import List, Dict, Any


def get_valid_region_list() -> List[str]:
    ec2_client = boto3.client("ec2")

    response = ec2_client.get_region_list(AllRegions=True)

    region_list = [region.get("RegionName") for region in response]

    return region_list


def validate_regions(*request_regions: str, event, context) -> bool:
    global valid_region_names

    scanned_regions = {}

    for region in request_regions:
        if region in validate_regions:
            if region in scanned_regions:
                send(event=event,
                     context=context,
                     responseStatus=FAILED,
                     reason=f"Failed: Duplicate Region in Replica Region List {region}"
                     )  # Send Failure duplicate Regions in request

                return False
        else:
            send(event=event,
                 context=context,
                 responseStatus=FAILED,
                 reason=f"Failed: Invalid / Unavailable Region {region} in Request"
                 )  # Send Failure: Invalid / Unavailable Region in request

            return False

    return True


kms_client = boto3.client("kms")

valid_region_names = get_valid_region_list()

def main(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
        Handles the creation of a key across many regions

        Properties:
          "MainKey":
            "Region": "string,
            "Policy":

          "ReplicaRegions":
            - String(s)


        Data :
            Outputs:
                Kms Key outputs of the keys made in the regions.

    :return: JSON response {statusCode: <>, body: <>}
    """

    properties = event.get('ResourceProperties', {})
    event_type = event.get('RequestType')

    if properties == {}:
        send(event=event,
             context=context,
             responseStatus=FAILED,
             reason="Failed: Properties Are Missing")  # Send Failure :- Properties missing

        return {
            "statusCode": 500,
            "body": {
                "message": "Failed: MainRegion Property missing"
            }
        }

    main_region = properties.get("MainRegion", "")

    if not validate_regions(main_region, event=event, context=context):
        return {
            "statusCode": 500,
            "body": {
                "message": "Failed: MainRegion Property Invalid"
            }
        }

    replica_regions = properties.get("ReplicaRegions", [""])

    if not validate_regions(*replica_regions, event=event, context=context):
        return {
            "statusCode": 500,
            "body": {
                "message": "Failed: MainRegion is Invalid"
            }
        }

    if main_region in replica_regions:
        send(event=event,
             context=context,
             responseStatus=FAILED,
             reason=f"Failed: Main Region mentioned in Replica region List"
             )  # Send Failure :- Main Region in replica region

        return {
            "statusCode": 500,
            "body": {
                "message": "Failed: MainRegion Cannot be in replica region"
            }
        }

    try :

        if event_type == "Create":
            kms_client.create_key(

            )

        elif event_type == "Update":
            send()

        elif event_type == "Delete":
            ...

        else:
            send()

            raise Exception(f"Invalid Event Type{event_type}")

    except Exception as e:

        ...

    return {
            "statusCode": 200,
            "body": {
                "message": f"Success made key in {main_region} with {len(replica_regions)} replica(s)"
            }
        }