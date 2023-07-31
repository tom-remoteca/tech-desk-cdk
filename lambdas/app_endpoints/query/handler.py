import os
import json
import boto3

from boto3.dynamodb.conditions import Key


# Create the DynamoDB client
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["CORE_TABLE_NAME"])
BUCKET_NAME = os.environ["BUCKET_NAME"]


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
    print(event)

    # Get Query ID from Path & MEO from URLarg
    query_id = event["pathParameters"]["query_id"]
    is_public = event["queryStringParameters"]["is_public"]
    user_id = event["requestContext"]["authorizer"]["sub"]
    company_id = event["requestContext"]["authorizer"]["tenant_id"]
    print(user_id, company_id, query_id, is_public)

    if event["httpMethod"] == "GET":
        return handle_get(
            company_id, user_id, query_id=query_id, is_public=is_public
        )

    # if event["httpMethod"] == "POST":
    #     return handle_post(company_id, user_id, event)
    return response(200)


def handle_get(company_id, user_id, query_id: str, is_public: bool):
    if is_public:
        primary_key_public = {
            "GSI1PK": f"COMPANY#{company_id}",
            "GSI1SK": f"PUBLIC#{is_public}QUERY#{query_id}",
        }
        res = table.query(
            IndexName="GSI1",
            KeyConditionExpression=Key("GSI1PK").eq(
                primary_key_public["GSI1PK"]
            )
            & Key("GSI1SK").eq(primary_key_public["GSI1SK"]),
        )
    else:
        primary_key_private = {
            "PK": f"COMPANY#{company_id}#USER#{user_id}",
            "SK": f"QUERY#{query_id}",
        }
        res = table.query(
            KeyConditionExpression=Key("PK").eq(primary_key_private["PK"])
            & Key("SK").eq(primary_key_private["SK"]),
        )
    print(res["Item"])
    return response(200, res["Item"]["query_data"])
