import os
import json
import boto3

from boto3.dynamodb.conditions import Key


# Create the DynamoDB client
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["CORE_TABLE_NAME"])


def response(status_code, body={}):
    if type(body) == str:
        body = {"data": body}
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
    user_id = event["requestContext"]["authorizer"]["sub"]
    notification_id = event["pathParameters"]["notification_id"]

    if event["httpMethod"] == "DELETE":
        return handle_delete(company_id, user_id, notification_id)

    return response(200)


def handle_delete(company_id, user_id, notification_id):
    # Constructing primary key
    primary_key = {
        "PK": f"COMPANY#{company_id}#USER#{user_id}",
        "SK": f"NOTIFICATION#{notification_id}",
    }

    # Making the delete call
    res = table.delete_item(Key=primary_key)

    print(res)

    # Checking if the deletion was successful
    if res.get("ResponseMetadata", {}).get("HTTPStatusCode") == 200:
        return response(200, "Deleted successfully.")
    else:
        return response(500, "Error occurred during deletion.")
