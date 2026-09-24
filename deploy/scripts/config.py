"""
    NAMES
"""

COMMON_NAME = "ka-me-ha-me-ha"

TEMPLATE_BUCKET_NAME   = f"{COMMON_NAME}--bootstrap-bucket"

BOOTSTRAP_STACK_NAME   = f"{COMMON_NAME}--bootstrap"

IAM_STACK_NAME         = f"{COMMON_NAME}--IAM"

KMS_MAIN_STACK_NAME    = f"{COMMON_NAME}--KMS-us-west-2"

KMS_REPLICA_STACK_NAME = f"{COMMON_NAME}--KMS-ap-south-1"

DYNAMODB_STACK_NAME    = f"{COMMON_NAME}--dynamodb"

LAMBDA_STACK_NAME      = f"{COMMON_NAME}--lambda"

S3_STACK_NAME          = f"{COMMON_NAME}--S3"

S3_BUCKET_NAME         = f"{COMMON_NAME}"

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


