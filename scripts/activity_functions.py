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


def update_query_activity(query_id, activity):
    print(f"Activity '{activity}' has been added to Query ID: {query_id}.")


def change_query_status(query_id, status):
    print(f"Status of Query ID {query_id} changed to '{status}'.")


def get_all_company_queries(company_id):
    print(f"getting all queries for {company_id}")
    res = core_table.query(
        IndexName="GSI1",
        KeyConditionExpression=Key("GSI1PK").eq(f"COMPANY#{company_id}")
        & Key("GSI1SK").begins_with("PUBLIC#"),
    )
    return [i["query_data"] for i in res.get("Items", [])]


def get_query(company_id, user_id, query_id):
    primary_key_private = {
        "PK": f"COMPANY#{company_id}#USER#{user_id}",
        "SK": f"QUERY#{query_id}",
    }
    res = core_table.query(
        KeyConditionExpression=Key("PK").eq(primary_key_private["PK"])
        & Key("SK").eq(primary_key_private["SK"]),
    )
    return res["Items"][0]["query_data"]


def change_status(company_id, query):
    print(company_id, query)
    status_map = {
        "created": [],
        "assigned": ["expert_image", "expert_name", "expert_description"],
        "scheduleConsultation": ["scheduler_url"],
        "consultationArranged": ["meeting_time", "meeting_url"],
        "inputScopeEngagement": ["scope_url"],
        "scopeAcceptance": ["scope_url"],
        "inputPayment": ["pay_instant_url", "pay_invoice_url"],
        "paymentComplete": ["payment_details", "invoice"],
        "commenceWriting": [],
        "completed": ["report_loc"],
        "expertComment": ["comment_content"],
        "techDeskComment": ["comment_content"],
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

        if new_status in ["assigned", "scheduleConsultation", "expertComment"]:
            questions = [
                {
                    "type": "list",
                    "name": "expert",
                    "message": "Select an expert",
                    "choices": agents.keys(),
                }
            ]
            answers = prompt(questions)
            agent = agents[answers["expert"]]
            if new_status == "assigned":
                answers = {
                    "expert_image": agent["image"],
                    "expert_name": agent["name"],
                    "expert_description": agent["description"],
                }
            elif new_status == "scheduleConsultation":
                answers = {
                    "scheduler_url": agent["calendar"],
                }
            elif new_status == "expertComment":
                questions = [
                    {
                        "type": "input",
                        "name": "comment_content",
                        "message": "Please input comment text",
                    }
                ]
                comment_answers = prompt(questions)
                answers = {
                    "commentor": agent["name"],
                    "commentor_image": agent["image"],
                    "comment_cotent": comment_answers["comment_content"],
                }
                new_status = "comment"

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
        sns_event = {
            "company_id": company_id,
            "author_id": query["submittor_id"],
            "query_id": query["query_id"],
            "event": new_status,
            **answers,
        }
        print(sns_event)
        publish_to_sns(json.dumps(sns_event))

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
