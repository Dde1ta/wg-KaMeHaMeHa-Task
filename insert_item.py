import time
import boto3

attacker = input("Enter the attacker: ")
defender = input("Enter the defender: ")

location = input("Where did this attack happen: ")
success = input("Was the attack successfull (y/n): ")
reason = input(f"Why was {defender} attacked: ")

timestamp = int(time.time())

dynamodb_client = boto3.client("dynamodb", region_name="us-west-2")

print("Adding to table")

respons = dynamodb_client.put_item(
	TableName="ka-me-ha-me-ha-archives",
	Item={
	"Attacker": {
		"S": attacker
		},
	"Defender": {
		"S": defender
		},
	"Location": {
		"S": location
		},
	"Reason": {
		"S": reason
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
print("Respons from client")

print(respons)
