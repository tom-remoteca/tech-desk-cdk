import os
import json
import time
import uuid
import boto3
import requests
from prompts import create_kwip_prompt, sanitise_kwip_response

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
    print(response.json())
    if response.status_code == 200:
        return response.json()["message"]["text"]
    else:
        print(response.status_code)
        print(response.json())
        return None


def log_query(
    company_id, user, user_id, ai_query_id, model, query, ai_response
):
    ai_query_data = {
        "model": model,
        "query": query,
        "response": ai_response,
        "ai_query_id": ai_query_id,
        "date": str(int(time.time())),
        "user": user,
        "user_id": user_id,
        "company_id": company_id,
    }

    table.put_item(
        Item={
            "PK": f"COMPANY#{company_id}#USER#{user_id}",
            "SK": f"AIQUERY#{ai_query_id}",
            "GSI1PK": f"COMPANY#{company_id}",
            "GSI1SK": f"AIQUERY#{ai_query_id}",
            "ai_query_data": ai_query_data,
        }
    )
    return


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
    user_name = event["requestContext"]["authorizer"]["name"]
    user_id = event["requestContext"]["authorizer"]["user_id"]
    company_id = event["requestContext"]["authorizer"]["company_id"]
    if event["httpMethod"] == "POST":
        return handle_post(company_id, user_id, user_name, event)
    return 200


def handle_post(company_id, user_id, user_name, event):
    aiquery_id = f"aiquery_{uuid.uuid4()}"
    print(event["body"])
    json_body = json.loads(event["body"])
    print(json_body)
    model = json_body.get("model")
    query = json_body.get("query")

    if not model or not query:
        return response(400, "Missing Model or query")

    # Create KWIP request body
    kwip_req_body = create_kwip_prompt(model, query)
    print(kwip_req_body)

    # Resolve Response from AI
    ai_response = ai_resolve(kwip_req_body)
    print(ai_response)

    # Remove reference to sources
    sanitised_ai_response = sanitise_kwip_response(
        model=model, ai_response=ai_response
    )
    print(sanitised_ai_response)

    # Log Query in DynamoDB
    log_query(
        company_id=company_id,
        user=user_name,
        user_id=user_id,
        ai_query_id=aiquery_id,
        model=model,
        query=query,
        ai_response=sanitised_ai_response,
    )

    if sanitised_ai_response:
        return response(200, sanitised_ai_response)
    else:
        return response(500, "Error - Please try again later")
