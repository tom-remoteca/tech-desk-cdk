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
    user_id = event["requestContext"]["authorizer"]["user_id"]
    company_id = event["requestContext"]["authorizer"]["company_id"]

    if event["httpMethod"] == "GET":
        return handle_get(company_id, user_id)

    return response(403, "Action not permitted")


def handle_get(company_id, user_id):
    primary_key_priv = {
        "PK": f"COMPANY#{company_id}#USER#{user_id}",
        "SK": "REPORT#",
    }

    response_priv = table.query(
        KeyConditionExpression=Key("PK").eq(primary_key_priv["PK"])
        & Key("SK").begins_with(primary_key_priv["SK"]),
    )

    # Define the primary key for public reports
    primary_key_public = {
        "PK": f"COMPANY#{company_id}#PUBLIC",
        "SK": "REPORT#",
    }

    response_priv = table.query(
        KeyConditionExpression=Key("PK").eq(primary_key_public["PK"])
        & Key("SK").begins_with(primary_key_public["SK"]),
    )

    # Extract the items (queries) from the responses and de-duplicate
    items_priv = response_priv["Items"]
    items_public = primary_key_public["Items"]

    report_ids = set([item["SK"] for item in items_priv])
    items_public = [item for item in items_public if item["SK"] not in report_ids]

    items = items_priv + items_public

    res = [item["query_data"] for item in items]

    return response(200, res)
