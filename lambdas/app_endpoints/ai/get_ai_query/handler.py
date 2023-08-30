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
    # user_id = event["requestContext"]["authorizer"]["user_id"]
    ai_query_id = event["pathParameters"]["ai_query_id"]
    company_id = event["requestContext"]["authorizer"]["company_id"]
    if event["httpMethod"] == "GET":
        return handle_get(company_id, ai_query_id)
    return 200


def handle_get(company_id, ai_query_id):
    primary_key = {
        "GSI1PK": f"COMPANY#{company_id}",
        "GSI1SK": f"AIQUERY#{ai_query_id}",
    }

    res = table.query(
        IndexName="GSI1",
        KeyConditionExpression=Key("GSI1PK").eq(primary_key["GSI1PK"])
        & Key("GSI1SK").eq(primary_key["GSI1SK"]),
    )
    if len(res["Items"]) > 0:
        return response(200, res["Items"][0].get("ai_query_data"))
    else:
        return response(403, "Unable to access this AI query.")
