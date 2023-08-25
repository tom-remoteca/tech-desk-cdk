import os
import json
import uuid
import boto3
from boto3.dynamodb.conditions import Key

# Create the DynamoDB client
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["CORE_TABLE_NAME"])


def response(status_code, body):
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
    print(event)
    company_id = event["requestContext"]["authorizer"]["tenant_id"]
    user_id = event["requestContext"]["authorizer"]["sub"]
    if event["httpMethod"] == "GET":
        return handle_get(company_id, user_id)
    return response(403, "Action not permitted")


def handle_get(company_id, user_id):
    # Define the primary key for user's own queries
    primary_key_user = {
        "PK": f"COMPANY#{company_id}#USER#{user_id}",
        "SK": "NOTIFICATION#",
    }

    projection_expression = "notification.#I, notification.is_public, \
                            notification.#D, notification.badge, \
                            notification.query_title, notification.query_id"

    # Execute the query for user's own queries
    res = table.query(
        KeyConditionExpression=Key("PK").eq(primary_key_user["PK"])
        & Key("SK").begins_with(primary_key_user["SK"]),
        ProjectionExpression=projection_expression,
        ExpressionAttributeNames={"#D": "date", "#I": "id"},
    )
    notifications = [item.get("notification") for item in res.get("Items", [])]

    return response(200, notifications)
