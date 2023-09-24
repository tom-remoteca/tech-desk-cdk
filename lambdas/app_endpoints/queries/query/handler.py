import os
import json
import boto3

from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError


# Create the DynamoDB client
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["CORE_TABLE_NAME"])
_lambda = boto3.client("lambda")

s3 = boto3.client("s3")
BUCKET = os.environ["BUCKET_NAME"]


def add_attachment_links(query_data):
    # Add signed urls to attachments
    for attachment in query_data.get("attachments", []):
        resp = _lambda.invoke(
            FunctionName=os.environ["SIGNED_URL_GENERATOR_FUNCTION_NAME"],
            Payload=json.dumps({"key": attachment["file_key"]}),
        )
        body = json.loads(resp["Payload"].read())
        attachment["signed_url"] = body["signed_url"]

    # Add signed urls to report assets
    for asset in query_data.get("report_details", {}).get("assets", []):
        resp = _lambda.invoke(
            FunctionName=os.environ["SIGNED_URL_GENERATOR_FUNCTION_NAME"],
            Payload=json.dumps({"key": asset["asset_key"]}),
        )
        body = json.loads(resp["Payload"].read())
        asset["signed_url"] = body["signed_url"]

    return query_data


def response(status_code, body={}):
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
    # Get Query ID from Path & MEO from URLarg
    query_id = event["pathParameters"]["query_id"]
    user_id = event["requestContext"]["authorizer"]["user_id"]
    company_id = event["requestContext"]["authorizer"]["company_id"]
    if event["httpMethod"] == "GET":
        return handle_get(company_id, user_id, query_id=query_id)
    return response(200)


def handle_get(company_id, user_id, query_id: str):
    # Attempt to retrieve using private keys
    primary_key_private = {
        "PK": f"COMPANY#{company_id}#USER#{user_id}",
        "SK": f"QUERY#{query_id}",
    }

    try:
        res = table.query(
            KeyConditionExpression=Key("PK").eq(primary_key_private["PK"])
            & Key("SK").eq(primary_key_private["SK"]),
        )

        # If an item is found using private keys, return
        if res["Items"]:
            query_data = res["Items"][0]["query_data"]
            query_data = add_attachment_links(query_data)
            return response(200, query_data)
    except ClientError:
        pass  # If there's an error, it'll proceed to the public key lookup

    # If nothing found with private keys, attempt to retrieve using public keys
    primary_key_public = {
        "PK": f"COMPANY#{company_id}#PUBLIC",
        "SK": f"QUERY#{query_id}",
    }

    try:
        res = table.query(
            KeyConditionExpression=Key("PK").eq(primary_key_public["PK"])
            & Key("SK").eq(primary_key_public["SK"]),
        )

        # If an item is found using public keys, return
        if res["Items"]:
            query_data = res["Items"][0]["query_data"]
            query_data = add_attachment_links(query_data)
            return response(200, query_data)
    except ClientError:
        pass  # You can handle the error as appropriate for your application

    # If neither private nor public returns an item, the user doesn't have access
    return response(403, "User doesn't have access to the query")
