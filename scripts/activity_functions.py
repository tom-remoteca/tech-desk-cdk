import time
import uuid
import json
from boto3.dynamodb.conditions import Key
from datetime import datetime, timedelta
from PyInquirer import prompt
from agents import agents

from mgmt_session import core_table, invite_table, users_table, publish_to_sns


def create_notification(company_id, query, badge):
    notification_id = f"notification_{uuid.uuid4()}"

    primary_keys = {
        "PK": f"COMPANY#{company_id}#USER#{query['submittor_id']}",
        "SK": f"NOTIFICATION#{notification_id}",
    }

    notification = {
        "id": notification_id,
        "is_public": query["is_public"],
        "date": int(time.time() * 1000),
        "badge": badge,
        "query_title": query["query_title"],
        "query_id": query["id"],
    }

    res = core_table.put_item(Item={**primary_keys, "notification": notification})
    return notification


def comment_as_expert(company_id, query):
    questions = [
        {
            "type": "list",
            "name": "expert",
            "message": "Select an expert",
            "choices": agents.keys(),
        },
        {
            "type": "input",
            "name": "comment_content",
            "message": "Please input comment text",
        },
    ]
    answers = prompt(questions)
    body = {
        "commentor": agents[answers["expert"]]["name"],
        "commentor_image": agents[answers["expert"]]["image"],
        "comment_content": answers["comment_content"],
    }
    sns_event = {
        "company_id": company_id,
        "author_id": query["submittor_id"],
        "query_id": query["query_id"],
        "event": "comment",
        **body,
    }
    print(sns_event)
    publish_to_sns(json.dumps(sns_event))
    create_notification(company_id=company_id, query=query, badge="New Comment!")
    return


def comment_as_techdesk(company_id, query):
    questions = [
        {
            "type": "input",
            "name": "comment_content",
            "message": "Please input techdesk comment text",
        },
    ]
    answers = prompt(questions)
    body = {
        "comment_content": answers["comment_content"],
    }
    sns_event = {
        "company_id": company_id,
        "author_id": query["submittor_id"],
        "query_id": query["query_id"],
        "event": "techDeskComment",
        **body,
    }
    print(sns_event)
    publish_to_sns(json.dumps(sns_event))
    create_notification(company_id=company_id, query=query, badge="New Comment!")
    return


def complete_add_report(company_id, query):
    questions = [
        {
            "type": "input",
            "name": "report_title",
            "message": "Report Title:",
        },
        {
            "type": "input",
            "name": "report_author",
            "message": "Report Author:",
        },
        {
            "type": "input",
            "name": "report_location_key",
            "message": "s3 key:",
        },
    ]
    report_id = f"report_{uuid.uuid4()}"
    answers = prompt(questions)

    if query["is_public"] == "true":
        suffix = "#PUBLIC"
    else:
        suffix = f"#USER#{query['submittor_id']}"

    primary_keys = {
        "PK": f"COMPANY#{company_id}{suffix}",
        "SK": f"REPORT#{report_id}",
        "GSI1PK": f"COMPANY#{company_id}",
        "GSI1SK": f"REPORT#{report_id}",
    }

    report_data = {
        "id": report_id,
        "report_title": answers["report_title"],
        "report_author": answers["report_author"],
        "report_loc": answers["report_location_key"],
        "query_id": query["id"],
        "date": int(time.time() * 1000),
    }

    core_table.put_item(
        Item={
            **primary_keys,
            "report_data": report_data,
        }
    )

    # Update status to complete
    sns_event = {
        "event": "completed",
        "company_id": company_id,
        "query_id": query["query_id"],
        "author_id": query["submittor_id"],
    }
    print(sns_event)
    publish_to_sns(json.dumps(sns_event))
    update_query_dynamo(query=query, field="report_details", data=report_data)
    return


def get_all_company_queries(company_id):
    print(f"getting all queries for {company_id}")
    res = core_table.query(
        IndexName="GSI1",
        KeyConditionExpression=Key("GSI1PK").eq(f"COMPANY#{company_id}")
        & Key("GSI1SK").begins_with("QUERY#"),
    )
    return [i["query_data"] for i in res.get("Items", [])]


def get_query(company_id, user_id, query_id):
    # First, search using GSI to find the correct PK and SK
    response = core_table.query(
        IndexName="GSI1",
        KeyConditionExpression="GSI1PK = :gsi1pk AND GSI1SK = :gsi1sk",
        ExpressionAttributeValues={
            ":gsi1pk": f"COMPANY#{company_id}",
            ":gsi1sk": f"QUERY#{query_id}",
        },
    )

    if "Items" not in response or len(response["Items"]) == 0:
        print("No matching item found.")
        return

    return response["Items"][0]["query_data"]


def parse_update_query_data(status, answers):
    if status == "assigned":
        return "expert_details", {
            "expert_image": answers["expert_image"],
            "expert_name": answers["expert_name"],
            "expert_description": answers["expert_description"],
            "expert_calendar": answers["expert_calendar"],
        }
    elif status == "consultationArranged":
        return "consultation_details", {
            "meeting_time": answers["meeting_time"],
            "meeting_url": answers["meeting_url"],
        }
    elif status == "inputScopeEngagement":
        return "scope_details", {
            "scope_url": answers["scope_url"],
        }
    elif status == "inputPayment":
        return "payment_details", {
            "pay_instant_url": answers["pay_instant_url"],
            "pay_invoice_url": answers["pay_invoice_url"],
        }
    elif status == "completed":
        return "report_details", {
            "report_title": answers["report_title"],
            "report_author": answers["report_author"],
            "report_loc": answers["report_loc"],
        }
    return None, None


def update_query_dynamo(query, field, data):
    # Now that we have the correct PK and SK, perform the update
    update_expression = f"SET query_data.{field} = :new_data"
    expression_attribute_values = {":new_data": data}

    if query["is_public"] == "true":
        suffix = "PUBLIC"
    else:
        suffix = f'USER#{query["submittor_id"]}'

    keys = {
        "PK": f"COMPANY#{query['company_id']}#{suffix}",
        "SK": f"QUERY#{query['query_id']}",
    }

    update_response = core_table.update_item(
        Key=keys,
        UpdateExpression=update_expression,
        ExpressionAttributeValues=expression_attribute_values,
    )

    print(update_response)


def change_status(company_id, query):
    print(company_id, query)
    status_map = {
        "created": [],
        "assigned": ["expert_image", "expert_name", "expert_description"],
        "scheduleConsultation": [],
        "consultationArranged": ["meeting_time", "meeting_url"],
        "inputScopeEngagement": ["scope_url"],
        "scopeAcceptance": [],
        "inputPayment": ["pay_instant_url", "pay_invoice_url"],
        "paymentComplete": [],
        "commenceWriting": [],
        "completed": [],
        "Exit": [],
    }
    while True:
        questions = [
            {
                "type": "list",
                "name": "status",
                "message": f"Choose new status. Current Status -- {query['query_status']}",
                "choices": status_map.keys(),
            }
        ]
        answers = prompt(questions)
        new_status = answers["status"]

        if new_status == "Exit":
            break
        if new_status == "assigned":
            questions = [
                {
                    "type": "list",
                    "name": "expert",
                    "message": "Select an expert",
                    "choices": agents.keys(),
                }
            ]
            answers = prompt(questions)
            print(answers)
            agent = agents[answers["expert"]]
            if new_status == "assigned":
                answers = {
                    "expert_image": agent["image"],
                    "expert_name": agent["name"],
                    "expert_description": agent["description"],
                    "expert_calendar": agent["calendar"],
                }
        else:
            questions = []
            for required_field in status_map[new_status]:
                questions.append(
                    {
                        "type": "input",
                        "name": required_field,
                        "message": f"Please input {required_field}",
                    }
                )
            answers = prompt(questions)

        # add details to the query in dynamo.
        query_field, query_field_details = parse_update_query_data(
            status=new_status, answers=answers
        )
        if query_field:
            update_query_dynamo(
                query=query, field=query_field, data=query_field_details
            )
            print("added field")

        # Create activity & update status
        sns_event = {
            "company_id": company_id,
            "author_id": query["submittor_id"],
            "query_id": query["query_id"],
            "event": new_status,
        }
        publish_to_sns(json.dumps(sns_event))

        # Add notification
        notification_badge = {
            "created": "Created",
            "assigned": "Assigned",
            "scheduleConsultation": "Schedule Consultation",
            # "consultationArranged": ["meeting_time", "meeting_url"],
            "inputScopeEngagement": "Engagement Attached",
            # "scopeAcceptance": ["scope_url"],
            "inputPayment": "Payment Required",
            # "paymentComplete": ["payment_details", "invoice"],
            # "commenceWriting": "",
            "completed": "Paper Complete",
            "comment": "New Comments",
            "expertComment": "New Comments",
            "techDeskComment": "New Comments",
        }
        if notification_badge.get(new_status, None):
            create_notification(
                company_id=company_id, query=query, badge=notification_badge[new_status]
            )
            print("Notification!")


def parse_action(status, message):
    """Parse and return action details based on status."""
    actions = {
        "scheduleConsultation": {"scheduler_url": message["scheduler_url"]},
        "consultationArranged": {
            "meeting_time": message["meeting_time"],
            "meeting_url": message["meeting_url"],
        },
        "inputScopeEngagement": {"scope_url": message["scope_url"]},
        "inputPayment": {
            "pay_instant_url": message["pay_instant_url"],
            "pay_invoice_url": message["pay_invoice_url"],
        },
    }
    return actions.get(status, {})
