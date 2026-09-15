import logging
import boto3
from typing import List, Dict, Any
from cfnresponse import send, SUCCESS, FAILED

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def fetch_parameter(name: str, decrypt: bool, client) -> str | List[str] | None:
    """Fetches a single parameter from AWS SSM Parameter Store."""
    try:
        response = client.get_parameter(
            Name=name,
            WithDecryption=decrypt
        )
        return response['Parameter']['Value']
    except Exception as e:
        logger.error(f"Error fetching parameter {name}: {str(e)}")
        raise e

def safe_boolean(value: Any) -> bool:
    """Safely parses a boolean value from CloudFormation (handles both str and bool types)."""
    if isinstance(value, str):
        return value.lower() in ["true", "yes", "1"]
    return bool(value)

def main(event, context):
    logger.info(f"Received event: {event}")
    
    # Establish a stable Physical Resource ID for CloudFormation
    physical_id = event.get('PhysicalResourceId', f"SSMParameterFetcher-{context.log_stream_name}")
    
    try:
        request_type = event.get('RequestType')
        properties = event.get('ResourceProperties', {})
        
        # 1. Handle Delete immediately
        if request_type == "Delete":
            logger.info("Delete event received. Nothing to delete, returning SUCCESS.")
            send(event, context, SUCCESS, {}, physicalResourceId=physical_id)
            return {"statusCode": 200, "body": "Deleted successfully"}

        # 2. Validate Properties
        if not properties:
            raise ValueError("Resource Properties are completely missing from the event.")

        parameter_region = properties.get("Region")
        parameters = properties.get("Parameters")

        if not parameter_region or not isinstance(parameter_region, str):
            raise ValueError(f"Region is missing or invalid: {parameter_region}")

        if not parameters or not isinstance(parameters, list):
            raise ValueError("Parameters list is missing, empty, or invalid.")

        # 3. Process Parameters (Create / Update)
        logger.info(f"Connecting to SSM in region: {parameter_region}")
        client = boto3.client('ssm', region_name=parameter_region)
        response_data = {}

        for param_dict in parameters:
            # param_dict looks like: {"MyOutputName": {"Name": "/my/param", "Decrypt": True}}
            if not isinstance(param_dict, dict) or not param_dict:
                continue
                
            output_name = list(param_dict.keys())[0]
            param_config = param_dict[output_name]
            
            param_name = param_config.get("Name")
            if not param_name:
                raise ValueError(f"Missing 'Name' for parameter output: {output_name}")
                
            param_decrypt = safe_boolean(param_config.get("Decrypt", False))

            logger.info(f"Fetching parameter: {param_name} (Decrypt: {param_decrypt})")
            param_value = fetch_parameter(param_name, param_decrypt, client)
            
            response_data[output_name] = param_value

        # 4. Send Success to CloudFormation
        logger.info("Successfully fetched all parameters. Sending SUCCESS to CloudFormation.")
        send(
            event, 
            context, 
            SUCCESS, 
            responseData=response_data, 
            physicalResourceId=physical_id
        )
        
        return {
            "statusCode": 200,
            "body": "Parameters fetched successfully"
        }

    except Exception as e:
        logger.error(f"Failed to process Custom Resource: {str(e)}", exc_info=True)
        # Send Failure to CloudFormation to prevent the stack from hanging
        send(
            event, 
            context, 
            FAILED, 
            responseData={}, 
            physicalResourceId=physical_id, 
            reason=str(e)
        )
        
        return {
            "statusCode": 500,
            "body": f"Failed: {str(e)}"
        }