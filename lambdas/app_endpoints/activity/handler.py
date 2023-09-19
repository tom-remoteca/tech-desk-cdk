import os
import json
import uuid
import boto3
import requests
from datetime import datetime

from boto3.dynamodb.conditions import Key

# Create the DynamoDB client
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["CORE_TABLE_NAME"])


def update_fd_query(query, message_obj):
    url = f"https://remotecalimited.freshdesk.com/api/v2/tickets/{query['query_data']['ticket_id']}/reply"

    headers = {"Content-Type": "application/json"}
    auth = ("CwDi38QwCfnAoWAFsy", "X")

    html_content = ""
    for key, value in message_obj.items():
        html_content += f"<strong>{key}</strong>: {value}<br/>"

    data = {"body": html_content}
    response = requests.post(url, headers=headers, auth=auth, data=json.dumps(data))
    print(response)
    return


def create_activity_dynamo(query, activity_status, activity_data={}):
    activity_id = f"activity_{uuid.uuid4()}"
    activity_data["event"] = activity_status
    activity_data["datetime"] = (int((datetime.now()).timestamp()),)

    res = table.put_item(
        Item={
            "PK": f"COMPANY#{query['query_data']['company_id']}#QUERY#{query['query_data']['id']}",
            "SK": f"ACTIVITY#{activity_id}",
            "activity": activity_data,
        }
    )

    return activity_data


def update_status(query, status):
    if status in ["techDeskComment", "comment"]:
        return

    keys = {"PK": query["PK"], "SK": query["SK"]}

    update_expression = "SET query_data.query_status = :new_status"
    expression_attribute_values = {":new_status": status}

    # Update item in DynamoDB
    response = table.update_item(
        Key=keys,
        UpdateExpression=update_expression,
        ExpressionAttributeValues=expression_attribute_values,
    )
    print(response)


def handle_sns(message):
    company_id = message["company_id"]
    query_id = message["query_id"]

    status = message.get("event")

    response = table.query(
        IndexName="GSI1",
        KeyConditionExpression="GSI1PK = :gsi1pk AND GSI1SK = :gsi1sk",
        ExpressionAttributeValues={
            ":gsi1pk": f"COMPANY#{company_id}",
            ":gsi1sk": f"QUERY#{query_id}",
        },
    )
    query = response["Items"][0]

    if status in [
        "created",
        "commenceWriting",
        "assigned",
        "scopeAcceptance",
        "paymentComplete",
        "completed",
        "techDeskComment",
        "comment",
    ]:
        activity_data = {}
        if status == "techDeskComment":
            activity_data["comment_content"] = message["comment_content"]
        if status == "comment":
            activity_data["commentor"] = message["commentor"]
            activity_data["comment_content"] = message["comment_content"]
            activity_data["commentor_image"] = message["commentor_image"]
        create_activity_dynamo(
            query=query, activity_status=status, activity_data=activity_data
        )

    update_status(query=query, status=status)
    print("status updated")
    update_fd_query(query=query, message_obj={"status": status})
    print("fd updated")


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
    # Handle SNS notifications
    if event.get("Records"):
        records = event.get("Records")
        for record in records:
            message = json.loads(record.get("Sns", {}).get("Message", {}))
            print(message)
            handle_sns(message)

    # Handle API GW requests
    else:
        company_id = event["requestContext"]["authorizer"]["company_id"]
        query_id = event["pathParameters"]["query_id"]

        if event["httpMethod"] == "GET":
            return handle_get(company_id, query_id)

        elif event["httpMethod"] == "POST":
            return handle_post(company_id, query_id, event)

        else:
            return response(403, "Action not permitted")


def handle_post(company_id, query_id, event):
    body = json.loads(event["body"])
    event_status = body["event"]

    res = table.query(
        IndexName="GSI1",
        KeyConditionExpression="GSI1PK = :gsi1pk AND GSI1SK = :gsi1sk",
        ExpressionAttributeValues={
            ":gsi1pk": f"COMPANY#{company_id}",
            ":gsi1sk": f"QUERY#{query_id}",
        },
    )
    query = res["Items"][0]

    if event_status == "comment":
        activity_data = {
            "commentor": event["requestContext"]["authorizer"]["name"],
            "comment_content": body["comment_body"],
            "commentor_image": event["requestContext"]["authorizer"]["picture"],
        }

    if activity_data:
        create_activity_dynamo(
            query=query,
            activity_status=event_status,
            activity_data=activity_data,
        )
        update_fd_query(
            query=query, message_obj={"status": event_status, **activity_data}
        )
        return response(200, activity_data)

    return response(400, "")


def handle_get(company_id, query_id):
    primary_key = {
        "PK": f"COMPANY#{company_id}#QUERY#{query_id}",
        "SK": "ACTIVITY#",
    }

    res = table.query(
        KeyConditionExpression=Key("PK").eq(primary_key["PK"])
        & Key("SK").begins_with(primary_key["SK"]),
    )

    all_activity = [item["activity"] for item in res.get("Items", [])]
    print(all_activity)
    return response(200, all_activity)
