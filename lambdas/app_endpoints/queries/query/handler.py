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
    # Collect keys from attachments and report assets
    attachment_keys = [
        attachment["file_key"] for attachment in query_data.get("attachments", [])
    ]
    asset_keys = [
        asset["asset_key"]
        for asset in query_data.get("report_details", {}).get("assets", [])
    ]
    all_keys = attachment_keys + asset_keys

    print(all_keys)
    # Make a single lambda call if there are keys to process
    if all_keys:
        resp = _lambda.invoke(
            FunctionName=os.environ["SIGNED_URL_GENERATOR_FUNCTION_NAME"],
            Payload=json.dumps({"keys": all_keys}),
        )
        body = json.loads(resp["Payload"].read())
        print(body)
        # Update each attachment with its signed URL
        for attachment in query_data.get("attachments", []):
            file_key = attachment["file_key"]
            if file_key in body:
                attachment["signed_url"] = body[file_key]["signed_url"]

        # Update each asset with its signed URL
        for asset in query_data.get("report_details", {}).get("assets", []):
            asset_key = asset["asset_key"]
            if asset_key in body:
                asset["signed_url"] = body[asset_key]["signed_url"]

    return query_data


# def add_attachment_links(query_data):
#     # Collect all keys from the attachments
#     keys = [attachment["file_key"] for attachment in query_data.get("attachments", [])]

#     # Make a single lambda call if there are keys to process
#     if keys:
#         resp = _lambda.invoke(
#             FunctionName=os.environ["SIGNED_URL_GENERATOR_FUNCTION_NAME"],
#             Payload=json.dumps({"keys": keys}),
#         )
#         body = json.loads(resp["Payload"].read())

#         # Update each attachment with its signed URL
#         for attachment in query_data.get("attachments", []):
#             file_key = attachment["file_key"]
#             if file_key in body:
#                 attachment["signed_url"] = body[file_key]["signed_url"]

#     # Collect all keys from the report assets

#     asset_keys = [
#         asset["asset_key"]
#         for asset in query_data.get("report_details", {}).get("assets", [])
#     ]

#     # Make a single lambda call if there are asset keys to process
#     if asset_keys:
#         resp = _lambda.invoke(
#             FunctionName=os.environ["SIGNED_URL_GENERATOR_FUNCTION_NAME"],
#             Payload=json.dumps({"keys": asset_keys}),
#         )
#         body = json.loads(resp["Payload"].read())

#         # Update each asset with its signed URL
#         for asset in query_data.get("report_details", {}).get("assets", []):
#             asset_key = asset["asset_key"]
#             if asset_key in body:
#                 asset["signed_url"] = body[asset_key]["signed_url"]

#     return query_data


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
        print("q-ed")
        # If an item is found using private keys, return
        if res["Items"]:
            query_data = res["Items"][0]["query_data"]
            query_data = add_attachment_links(query_data)
            print("attachmented")
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
        print("q-ed pub")

        # If an item is found using public keys, return
        if res["Items"]:
            query_data = res["Items"][0]["query_data"]
            query_data = add_attachment_links(query_data)
            print("attachmented")
            return response(200, query_data)
    except ClientError:
        pass
    return response(403, "User doesn't have access to the query")
