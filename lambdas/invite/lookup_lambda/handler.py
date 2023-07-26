import os
import json
import boto3
from botocore.exceptions import ClientError


# Create the DynamoDB client
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["INVITE_TABLE_NAME"])


def handler(event, context):
    print(event)
    # Get the inviteToken from the queryStringParameters
    inviteToken = event["queryStringParameters"].get("inviteToken")

    if not inviteToken:
        return {
            "statusCode": 400,
            "body": json.dumps("inviteToken is required"),
        }

    try:
        # Fetch the item from DynamoDB
        response = table.get_item(Key={"inviteToken": inviteToken})
    except ClientError as e:
        print(e.response["Error"]["Message"])
        return {
            "statusCode": 500,
            "body": json.dumps("Error fetching item from DynamoDB"),
        }
    # If the item doesn't exist, return an error
    if "Item" not in response:
        return {
            "statusCode": 404,
            "body": json.dumps("inviteToken expired or incorrect."),
        }
    print(response["Item"])
    response["Item"]["expiration_time"] = float(
        response["Item"]["expiration_time"])
    return {
        "statusCode": 200,
        "body": json.dumps(response["Item"]),
    }
