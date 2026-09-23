import time
import boto3
from uuid import uuid7  # pip install uuid6

attacker = input("Enter the attacker: ")
attacker_class = input("Enter the Class of the attacker: ")

defender = input("Enter the defender: ")
defender_class = input("Enter the class of the defender: ")

location = input("Where did this attack happen: ")
success = input("Was the attack successful (y/n): ")

reason = input(f"Why was {defender} attack by {attacker}: ")
damage = input(f"How much damage was dealt to {defender}(Express in numbers): ")

timestamp = int(time.time() * 1000)

# Construct the composite Sort Key
sort_key = f"{defender_class}#{defender}#{timestamp}"

us_west_2_session = boto3.Session(region_name="us-west-2", profile_name="test-chahal")
dynamodb_client = us_west_2_session.client("dynamodb")

print("Adding to table")

response = dynamodb_client.put_item(
    TableName="ka-me-ha-me-ha-archives",
    Item={
        "Attacker": {
            "S": f"{attacker_class}#{attacker}"
        },
        "DefenderTimestamp": {
            "S": sort_key
        },
        "Location": {
            "S": location
        },
        "Success": {
            "BOOL": success.lower() == 'y'
        },
        "Reason": {
            "S": reason
        },
        "Damage": {
            "N": damage
        }
    }
)

print(f"Success! Attack logged with SK: {sort_key}")
