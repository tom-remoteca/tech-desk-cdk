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


def add_attachment_links(report_data):
    assets = report_data.get("assets", [])
    for assets in assets:
        resp = _lambda.invoke(
            FunctionName=os.environ["SIGNED_URL_GENERATOR_FUNCTION_NAME"],
            Payload=json.dumps({"key": assets["file_key"]}),
        )
        body = json.loads(resp["Payload"].read())
        print(body)

        assets["signed_url"] = body["signed_url"]

    return report_data


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
    report_id = event["pathParameters"]["report_id"]
    company_id = event["requestContext"]["authorizer"]["company_id"]
    user_id = event["requestContext"]["authorizer"]["user_id"]
    if event["httpMethod"] == "GET":
        return handle_get(company_id, user_id, report_id=report_id)
    return response(200)


def handle_get(company_id, user_id, report_id: str):
    # Attempt to retrieve using private keys
    primary_key_private = {
        "PK": f"COMPANY#{company_id}#USER#{user_id}",
        "SK": f"REPORT#{report_id}",
    }

    try:
        res = table.query(
            KeyConditionExpression=Key("PK").eq(primary_key_private["PK"])
            & Key("SK").eq(primary_key_private["SK"]),
        )

        # If an item is found using private keys, return
        if res["Items"]:
            report_data = res["Items"][0]["report_data"]
            report_data = add_attachment_links(report_data)
            return response(200, report_data)
    except ClientError:
        pass  # If there's an error, it'll proceed to the public key lookup

    # If nothing found with private keys, attempt to retrieve using public keys
    primary_key_public = {
        "PK": f"COMPANY#{company_id}#PUBLIC",
        "SK": f"REPORT#{report_id}",
    }

    try:
        res = table.query(
            KeyConditionExpression=Key("PK").eq(primary_key_public["PK"])
            & Key("SK").eq(primary_key_public["SK"]),
        )

        # If an item is found using public keys, return
        if res["Items"]:
            report_data = res["Items"][0]["report_data"]
            report_data = add_attachment_links(report_data)
            return response(200, report_data)
    except ClientError:
        pass  # You can handle the error as appropriate for your application

    return response(403, "User doesn't have access to the report")
