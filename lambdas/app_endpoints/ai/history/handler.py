import os
import json
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
    user_id = event["requestContext"]["authorizer"]["sub"]
    company_id = event["requestContext"]["authorizer"]["company_id"]
    if event["httpMethod"] == "GET":
        return handle_get(company_id, user_id)
    return 200


def handle_get(company_id, user_id):
    # Define the primary key for user's own queries
    primary_key_user = {
        "PK": f"COMPANY#{company_id}#USER#{user_id}",
        "SK": "AIQUERY",
    }

    # Execute the query for user's own queries
    res = table.query(
        KeyConditionExpression=Key("PK").eq(primary_key_user["PK"])
        & Key("SK").begins_with(primary_key_user["SK"])
    )

    # Extract the items (queries) from the responses and de-duplicate
    users_ai_queries = [item.get("ai_query_data") for item in res["Items"]]

    return response(200, users_ai_queries)
