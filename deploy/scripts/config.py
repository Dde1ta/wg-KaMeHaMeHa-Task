"""
    NAMES
"""

TEMPLATE_BUCKET_NAME   = "ka-me-ha-me-ha--bootstrap-bucket"

BOOTSTRAP_STACK_NAME   = "ka-me-ha-me-ha--bootstrap"

IAM_STACK_NAME         = "ka-me-ha-me-ha--IAM"

KMS_MAIN_STACK_NAME    = "ka-me-ha-me-ha--KMS-us-west-2"

KMS_REPLICA_STACK_NAME = "ka-me-ha-me-ha--KMS-ap-south-1"

DYNAMODB_STACK_NAME    = "ka-me-ha-me-ha--dynamodb"

LAMBDA_STACK_NAME      = "ka-me-ha-me-ha--lambda"

S3_STACK_NAME          = "ka-me-ha-me-ha--S3"

S3_BUCKET_NAME         = "ka-me-ha-me-ha"

OBJECTIVE_FILE         = "teenage-mutant-ninja-turtles.json"

"""
   TEMPLATES 
"""

US_WEST_2_TEMPLATE_PATHS = {
    KMS_MAIN_STACK_NAME:    "deploy/templates/Keys.yaml",
    DYNAMODB_STACK_NAME:    "deploy/templates/DynamoDB.yaml",
    LAMBDA_STACK_NAME:      "deploy/templates/Lambda.yaml",
    S3_STACK_NAME:          "deploy/templates/S3-encrypted.yaml",
    IAM_STACK_NAME:         "deploy/templates/IAM.yaml",
    BOOTSTRAP_STACK_NAME:   "deploy/templates/S3.yaml"
}

AP_SOUTH_1_TEMPLATE_PATHS = {
    KMS_REPLICA_STACK_NAME: "deploy/templates/Keys.yaml",
    S3_STACK_NAME:          "deploy/templates/S3-encrypted.yaml",
    BOOTSTRAP_STACK_NAME:   "deploy/templates/S3.yaml"
}


"""
    CODE ZIPS
"""

CODE_ZIPS_PATH = {
    LAMBDA_STACK_NAME:      "deploy/zips/lambda-code.zip"
}

"""
REGION
"""
