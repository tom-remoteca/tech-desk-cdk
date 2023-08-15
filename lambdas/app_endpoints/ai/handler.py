import os
import json
import boto3
import requests
from prompts import create_kwip_prompt

# Create the DynamoDB client
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["CORE_TABLE_NAME"])


def ai_resolve(kwip_req_body):
    url = "https://api.kwip.ai/v1/generate"

    payload = json.dumps(kwip_req_body)
    headers = {
        "x-api-key": "WzQl4o9mHv2EbLfuXgVR8NpQrhCVj3i6wQYlu7sd",
        "Content-Type": "application/json",
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    return response.json()["message"]["text"]


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
    print(user_id)
    if event["httpMethod"] == "GET":
        return handle_get(company_id, user_id, event)
    return 200


def handle_get(company_id, user_id, event):
    model = event["queryStringParameters"].get("model")
    query = event["queryStringParameters"].get("query")

    kwip_req_body = create_kwip_prompt(model, query)
    print(kwip_req_body)
    return response(200, ai_resolve(kwip_req_body))
