import os
import cgi
import json
import uuid
import boto3
import time
import base64
from io import BytesIO

from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError


# Create the DynamoDB client
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["CORE_TABLE_NAME"])
BUCKET_NAME = os.environ["BUCKET_NAME"]


def response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "OPTIONS,POST,GET",
        },
        "body": json.dumps(body, default=str)
    }


def handler(event, context):
    print(event)
    # Get Query ID from Path & MEO from URLarg
    query_id = 'lemon'
    is_public = 'true'
    user_id = event['requestContext']['authorizer']['sub']
    company_id = event['requestContext']['authorizer']['tenant_id']

    if event["httpMethod"] == "GET":
        return handle_get(company_id, user_id, event)
        
    # if event["httpMethod"] == "POST":
    #     return handle_post(company_id, user_id, event)
    return 200



def handle_get(company_id, user_id, event):
    # Define the primary key for user's own queries
    primary_key_user = {
        'PK': f'COMPANY#{company_id}#USER#{user_id}',
    }

    # Execute the query for user's own queries
    response_user = table.query(
        KeyConditionExpression=boto3.dynamodb.conditions.Key('PK').eq(primary_key_user['PK']),
    )

    # Define the primary key for public queries
    primary_key_public = {
        'GSI1PK': f'COMPANY#{company_id}',
        'GSI1SK': f'PUBLIC#TRUE',
    }

    # Execute the query for public queries
    response_public = table.query(
        IndexName="GSI1",  # replace with your GSI name
        KeyConditionExpression=boto3.dynamodb.conditions.Key('GSI1PK').eq(primary_key_public['GSI1PK']) & 
                               boto3.dynamodb.conditions.Key('GSI1SK').begins_with(primary_key_public['GSI1SK']),
        ProjectionExpression=projection_expression,
    )

    # Extract the items (queries) from the responses and de-duplicate
    items_user = response_user['Items']
    items_public = response_public['Items']

    query_ids = set([item['SK'] for item in items_user])
    items_public = [item for item in items_public if item['SK'] not in query_ids]

    items = items_user + items_public

    res = [item['query_data'] for item in items]

    return response(200, res)
