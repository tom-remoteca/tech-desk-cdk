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


def parse_activity(status, raw_activity):
    activity_data = {
        "event": status,
        "datetime": int((datetime.now()).timestamp()),
    }
    if status == "assigned":
        activity_data["expert_image"] = raw_activity["expert_image"]
        activity_data["expert_name"] = raw_activity["expert_name"]
        activity_data["expert_description"] = raw_activity["expert_description"]

    elif status == "scopeAcceptance":
        activity_data["scope_url"] = raw_activity["scope_url"]

    elif status == "paymentComplete":
        activity_data["payment_details"] = raw_activity["payment_details"]
        activity_data["invoice"] = raw_activity["invoice"]

    elif status == "completed":
        activity_data["report_title"] = raw_activity["report_title"]
        activity_data["report_author"] = raw_activity["report_author"]
        activity_data["report_loc"] = raw_activity["report_loc"]

    elif status == "comment":
        activity_data["commentor"] = raw_activity["commentor"]
        activity_data["commentor_image"] = raw_activity["commentor_image"]
        activity_data["comment_content"] = raw_activity["comment_content"]

    elif status == "techDeskComment":
        activity_data["comment_content"] = raw_activity["comment_content"]

    return activity_data


def create_activity_dynamo(query, activity_data):
    activity_id = f"activity_{uuid.uuid4()}"

    res = table.put_item(
        Item={
            "PK": f"COMPANY#{query['query_data']['company_id']}#QUERY#{query['query_data']['id']}",
            "SK": f"ACTIVITY#{activity_id}",
            "activity": activity_data,
        }
    )

    return activity_data


def parse_action(status, message):
    if status == "scheduleConsultation":
        return {"scheduler_url": message["scheduler_url"]}
    elif status == "consultationArranged":
        return {
            "meeting_time": message["meeting_time"],
            "meeting_url": message["meeting_url"],
        }
    elif status == "inputScopeEngagement":
        return {
            "scope_url": message["scope_url"],
        }
    elif status == "inputPayment":
        return {
            "pay_instant_url": message["pay_instant_url"],
            "pay_invoice_url": message["pay_invoice_url"],
        }
    elif status == "completed":
        return {
            "report_title": message["report_title"],
            "report_author": message["report_author"],
            "report_loc": message["report_loc"],
        }


def update_action_dynamo(query, action_data):
    # Now that we have the correct PK and SK, perform the update
    update_expression = "SET query_data.action_data = :new_action_data"
    expression_attribute_values = {":new_action_data": action_data}

    update_response = table.update_item(
        Key={"PK": query["PK"], "SK": query["SK"]},
        UpdateExpression=update_expression,
        ExpressionAttributeValues=expression_attribute_values,
    )

    print(update_response)


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
        "comment",
        "techDeskComment",
    ]:
        activity_data = parse_activity(status=status, raw_activity=message)
        print(activity_data)

        create_activity_dynamo(
            query=query,
            activity_data=activity_data,
        )
        print("created activity in dynamo")

        if status not in [
            "comment",
            "techDeskComment",
        ]:
            update_action_dynamo(
                query=query,
                action_data={},
            )
            print("action reset")
    # Update action:
    if status in [
        "scheduleConsultation",
        "consultationArranged",
        "inputScopeEngagement",
        "inputPayment",
        "completed",
    ]:
        print("handle ACTION")
        action_data = parse_action(status, message)
        print(action_data)
        update_action_dynamo(
            query=query,
            action_data=action_data,
        )
        print("action updated.")

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
            "datetime": int((datetime.now()).timestamp()),
            "comment_content": body["comment_body"],
            "commentor_image": event["requestContext"]["authorizer"]["picture"],
            "event": "comment",
        }

    if activity_data:
        create_activity_dynamo(
            query=query,
            activity_data=activity_data,
        )
        update_fd_query(
            query=query, message_obj={"status": event_status, **activity_data}
        )
        print("fd updated")
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
