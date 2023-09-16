import os
import cgi
import json
import uuid
import boto3
import time
import base64
import requests
from io import BytesIO

from boto3.dynamodb.conditions import Key


# Create the DynamoDB client
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["CORE_TABLE_NAME"])

BUCKET_NAME = os.environ["BUCKET_NAME"]


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
    print(user_id)
    if event["httpMethod"] == "GET":
        return handle_get(company_id, user_id)

    return response(403, "Action not permitted")


def handle_get(company_id, user_id):
    # Define the primary key for user's own queries
    primary_key_user = {
        "PK": f"COMPANY#{company_id}#USER#{user_id}",
        "SK": "REPORT#",
    }

    projection_expression = "SK, report_data.title, report_data.author, \
                    report_data.completion_date, report_data.report_id"

    # Execute the query for user's own reports
    response_user = table.query(
        KeyConditionExpression=Key("PK").eq(primary_key_user["PK"])
        & Key("SK").begins_with(primary_key_user["SK"]),
        ProjectionExpression=projection_expression,
    )

    # Define the primary key for public reports
    primary_key_public = {
        "GSI1PK": f"COMPANY#{company_id}",
        "GSI1SK": "REPORT#PUBLIC#TRUE",
    }

    # Execute the query for public queries
    response_public = table.query(
        IndexName="GSI1",  # replace with your GSI name
        KeyConditionExpression=Key("GSI1PK").eq(primary_key_public["GSI1PK"])
        & Key("GSI1SK").begins_with(primary_key_public["GSI1SK"]),
        ProjectionExpression=projection_expression,
    )

    # Extract the items (queries) from the responses and de-duplicate
    items_user = response_user["Items"]
    items_public = response_public["Items"]

    query_ids = set([item["SK"] for item in items_user])
    items_public = [item for item in items_public if item["SK"] not in query_ids]

    items = items_user + items_public

    res = [item["query_data"] for item in items]

    return response(200, res)
