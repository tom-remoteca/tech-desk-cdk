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
    company_id = event["requestContext"]["authorizer"]["tenant_id"]
    is_admin = event["requestContext"]["authorizer"]["role"].lower() == "admin"

    if event["httpMethod"] == "GET":
        if is_admin:
            return handle_get(company_id)
        else:
            return response(403, "Unauthorised")
    return 200


def handle_get(company_id):
    # Define the primary key for public queries
    primary_key = {
        "GSI1PK": f"COMPANY#{company_id}",
        "GSI1SK": f"USER#",
    }

    # Execute the query for public queries
    res = table.query(
        IndexName="GSI1",  # replace with your GSI name
        KeyConditionExpression=Key("GSI1PK").eq(primary_key["GSI1PK"])
        & Key("GSI1SK").begins_with(primary_key["GSI1SK"]),
        ProjectionExpression="#N, image, email, #R, #I",  # email
        ExpressionAttributeNames={"#N": "name", "#R": "role", "#I": "id"},
    )
    users = res.get("Items", [])

    return response(200, users)
