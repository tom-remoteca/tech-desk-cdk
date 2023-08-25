import json
import os
import boto3
import uuid
from botocore.exceptions import ClientError
from datetime import datetime, timedelta

# Create the DynamoDB client
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["INVITE_TABLE_NAME"])


def response(status_code, body={}):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "OPTIONS,POST,GET",
        },
        "body": json.dumps(body, default=str),
    }


def handler(event, context):
    company_id = event["requestContext"]["authorizer"]["company_id"]
    company_name = event["requestContext"]["authorizer"]["company_name"]

    # Generate a UUID
    invite_token = str(uuid.uuid4())

    # Calculate the expiration time
    expiration_time = int((datetime.now() + timedelta(days=1)).timestamp())

    # Create the item
    item = {
        "inviteToken": invite_token,
        "company_id": company_id,
        "company_name": company_name,
        "expiration_time": expiration_time,
    }

    try:
        # Put the item into DynamoDB
        table.put_item(Item=item)
    except ClientError as e:
        print(e.response["Error"]["Message"])
        return response(500, "Error inserting item into DynamoDB")

    # Return the UUID and expiration time
    return response(200, item)
