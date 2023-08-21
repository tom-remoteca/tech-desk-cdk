import os
import json
import boto3
from boto3.dynamodb.conditions import Key

# Create the DynamoDB client
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["USERS_TABLE_NAME"])


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
    company_id = event["requestContext"]["authorizer"]["tenant_id"]
    is_admin = True
    if event["httpMethod"] == "GET":
        if is_admin:
            return handle_get(company_id)
        else:
            return response(403, "Unauthorised")
    return 200


def handle_get(company_id):
    projection_expression = "SK, query_data.id, query_data.is_public, \
                            query_data.query_title, query_data.query_status, \
                            query_data.date_submitted"

    # Define the primary key for public queries
    primary_key_public = {
        "GSI1PK": f"COMPANY#{company_id}",
    }

    # Execute the query for public queries
    res = table.query(
        IndexName="GSI1",  # replace with your GSI name
        KeyConditionExpression=Key("GSI1PK").eq(primary_key_public["GSI1PK"]),
        ProjectionExpression=projection_expression,
    )
    users = res.get("Items", [])

    return response(200, users)
