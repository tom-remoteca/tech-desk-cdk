import json
import requests


def dict_to_html(d):
    html_content = ""
    for key, value in d.items():
        html_content += f"<strong>{key}</strong>: {value}<br/>"
    return html_content


def create_freshdesk_ticket(request_body):
    url = "https://remotecalimited.freshdesk.com/api/v2/tickets"
    headers = {"Content-Type": "application/json"}
    auth = ("CwDi38QwCfnAoWAFsy", "X")
    ticket_desc = dict_to_html(request_body)
    data = {
        "description": ticket_desc,
        "subject": f"Sales Lead: {request_body.get('company', '')}",
        "email": "tom@remoteca.co.uk",
        "priority": 1,
        "status": 2,
    }
    response = requests.post(
        url, headers=headers, auth=auth, data=json.dumps(data)
    )
    return


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

    if event["httpMethod"] == "POST":
        return handle_post(event)
    return response(403, "Action not permitted")


def handle_post(event):
    request_body = json.loads(event.get("body", {}))

    # Send Contact US Form to FreshDesk
    create_freshdesk_ticket(request_body)

    return response(200, "Submitted")
