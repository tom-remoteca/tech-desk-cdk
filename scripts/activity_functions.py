import time
import uuid
import json
from boto3.dynamodb.conditions import Key
from datetime import datetime, timedelta
from PyInquirer import prompt


from mgmt_session import core_table, invite_table, users_table, publish_to_sns


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
        "comment": ["commentor", "commentor_image", "comment_cotent"],
    }
    questions = [
        {
            "type": "list",
            "name": "status",
            "message": f"Choose new status. Current Status {query['query_status']}",
            "choices": status_map.keys(),
        }
    ]
    answers = prompt(questions)
    new_status = answers["status"]
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
