import json
import os
import boto3
import uuid
from botocore.exceptions import ClientError
from datetime import datetime, timedelta

# Create the DynamoDB client
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["INVITE_TABLE_NAME"])


def handler(event, context):
    tenant_id = event.get("tenant_id", "company_exampleid1234567")
    tenant_name = event.get("tenant_name", "Example Company")

    # Generate a UUID
    invite_token = str(uuid.uuid4())

    # Calculate the expiration time
    expiration_time = int((datetime.now() + timedelta(days=1)).timestamp())

    # Create the item
    item = {
        "inviteToken": invite_token,
        "tenant_id": tenant_id,
        "tenant_name": tenant_name,
        "expiration_time": expiration_time,
    }

    try:
        # Put the item into DynamoDB
        table.put_item(Item=item)
    except ClientError as e:
        print(e.response["Error"]["Message"])
        return {
            "statusCode": 500,
            "body": json.dumps("Error inserting item into DynamoDB"),
        }

    # Return the UUID and expiration time
    return {
        "statusCode": 200,
        "body": json.dumps(item),
    }
