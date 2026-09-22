import time
import boto3
import uuid

attacker = input("Enter the attacker: ")
defender = input("Enter the defender: ")

location = input("Where did this attack happen: ")
success = input("Was the attack successfull (y/n): ")

timestamp = int(time.time())
AttackID = str(uuid.uuid4())

us_west_2_session = boto3.Session(region_name="us-west-2", profile_name="test-chahal")
dynamodb_client = us_west_2_session.client("dynamodb")

print("Adding to table")

response = dynamodb_client.put_item(
    TableName="ka-me-ha-me-ha-archives",
    Item={
        "AttackID": {
            "S": AttackID
        },
        "Attacker": {
            "S": attacker
        },
        "Defender": {
            "S": defender
        },
        "Location": {
            "S": location
        },
        "TimeStamp": {
            "N": str(timestamp)
        },
        "Success": {
            "BOOL": success == 'y'
        }
    }
)

print("Add to table")
print("Response from client")

print(response)
