import os
import cgi
import json
import uuid
import boto3
import time
import base64
import requests
from io import BytesIO

from boto3.dynamodb.conditions import Key


# Create the DynamoDB client
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["CORE_TABLE_NAME"])
sns = boto3.client("sns")

BUCKET_NAME = os.environ["BUCKET_NAME"]


def dict_to_html(d):
    html_content = ""
    for key, value in d.items():
        html_content += f"<strong>{key}</strong>: {value}<br/>"
    return html_content


def create_query_freshdesk(parsed_query):
    url = "https://remotecalimited.freshdesk.com/api/v2/tickets"
    headers = {"Content-Type": "application/json"}
    auth = ("CwDi38QwCfnAoWAFsy", "X")
    ticket_desc = dict_to_html(parsed_query)
    data = {
        "description": ticket_desc,
        "subject": f"{parsed_query['company_name']}: {parsed_query['query_title']}",
        "email": "tom@remoteca.co.uk",
        "priority": 1,
        "status": 2,
    }
    response = requests.post(url, headers=headers, auth=auth, data=json.dumps(data))
    if response.status_code == 201:  # 201 means "Created"
        response_data = (
            response.json()
        )  # This will give you the JSON object returned by Freshdesk
        ticket_id = response_data.get(
            "id"
        )  # Retrieve the ID of the ticket from the respons
        print(f"Ticket ID: {ticket_id}")
        return ticket_id
    else:
        print(
            f"Error creating ticket. Status Code: {response.status_code}, Response: {response.text}"
        )
        return None


def add_created_activity(company_id, query_id, user_id):
    message = {
        "company_id": company_id,
        "author_id": user_id,
        "query_id": query_id,
        "event": "created",
    }
    sns.publish(
        TopicArn=os.environ["ACTIVITY_TOPIC"],
        Message=json.dumps(message),
        # MessageStructure="json",
    )
    return


def write_file_to_s3(query_id, file_data):
    # print(file_data)
    # Initialize Boto3 S3 client
    s3_client = boto3.client("s3")

    attachment_id = f"attachment_{uuid.uuid4()}"

    file_key = f"queries/{query_id}/{attachment_id}"

    # Write the file to S3 bucket
    s3_client.upload_fileobj(
        file_data["file_data_bytes"],
        BUCKET_NAME,
        file_key,
        ExtraArgs={"ContentType": file_data["content_type"]},
    )
    return attachment_id, file_key


def parse_raw_query(query_id, event):
    # Decode base64 encoded data from the event
    encoded_data = event["body"]
    decoded_data = base64.b64decode(encoded_data)

    # Parse the content type and boundary from the 'Content-Type' header
    content_type_header = event["headers"]["content-type"]
    content_type, options = cgi.parse_header(content_type_header)
    # boundary = options.get("boundary")

    # Create a BytesIO object to use as the file pointer
    fp = BytesIO(decoded_data)

    # Create a FieldStorage object to parse the multipart form data
    fs = cgi.FieldStorage(
        fp=fp,
        headers=event["headers"],
        environ={"REQUEST_METHOD": "POST"},
        keep_blank_values=True,
    )

    # Dictionary to store the parsed form data
    form_data = {}

    # Iterate through each field in the multipart form data
    for field in fs.list:
        if field.filename:  # This is a file field
            form_data[field.name] = {
                "file_name": field.filename,
                "content_type": field.type,
                "file_data": field.file,  # Read the file data here
                "file_data_bytes": BytesIO(field.file.read()),
            }
        else:  # This is a regular form field
            form_data[field.name] = field.value
    print(form_data.keys())

    out = {}
    attachments = []
    out["query_id"] = query_id
    for k, v in form_data.items():
        if k.startswith("file-"):
            print("saving file to s3")
            attachment_id, file_key = write_file_to_s3(query_id=query_id, file_data=v)
            attachments.append(
                {
                    "file_name": v["file_name"],
                    "attachment_id": attachment_id,
                    "file_key": file_key,
                }
            )
            continue
        elif k == "usecase_tags":
            raw_tags = json.loads(v)
            tags = [obj["label"] for obj in raw_tags]
            out["usecase_tags"] = tags
        else:
            out[k] = v
    out["attachments"] = attachments
    return out


def create_query_dynamo(company_id, user_id, query_id, query_data):
    print(query_data)
    if query_data["is_public"] == "true":
        primary_keys = {
            "PK": f"COMPANY#{company_id}#PUBLIC",
            "SK": f"QUERY#{query_id}",
            "GSI1PK": f"COMPANY#{company_id}",
            "GSI1SK": f"QUERY#{query_id}",
        }
    else:
        primary_keys = {
            "PK": f"COMPANY#{company_id}#USER#{user_id}",
            "SK": f"QUERY#{query_id}",
            "GSI1PK": f"COMPANY#{company_id}",
            "GSI1SK": f"QUERY#{query_id}",
        }

    table.put_item(
        Item={
            **primary_keys,
            "query_data": query_data,
        }
    )

    return query_data


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
    user_id = event["requestContext"]["authorizer"]["user_id"]
    company_id = event["requestContext"]["authorizer"]["company_id"]
    print("UserID", user_id)
    if event["httpMethod"] == "GET":
        return handle_get(company_id, user_id)

    if event["httpMethod"] == "POST":
        return handle_post(company_id, user_id, event)
    return response(403, "Action not permitted")


def handle_post(company_id, user_id, event):
    query_id = f"query_{uuid.uuid4()}"
    print(query_id)

    # Process data in webkit form and save attachments to s3
    parsed_query = parse_raw_query(query_id, event)
    print("parsed raw")
    parsed_query["submittor_id"] = user_id
    parsed_query["submittor_email"] = event["requestContext"]["authorizer"]["email"]
    parsed_query["company_name"] = event["requestContext"]["authorizer"]["company_name"]
    parsed_query["company_id"] = event["requestContext"]["authorizer"]["company_id"]
    parsed_query["id"] = query_id
    parsed_query["date_submitted"] = str(int(time.time()))
    parsed_query["query_status"] = "created"
    parsed_query["company_id"] = company_id

    # Send Query to FreshDesk
    ticket_id = create_query_freshdesk(parsed_query)
    print("Submitted to freshdesk")

    if not ticket_id:
        return response(501, "E3012")

    parsed_query["ticket_id"] = ticket_id
    print(parsed_query)
    # Save this request to Dynamo
    create_query_dynamo(company_id, user_id, query_id, parsed_query)
    print("created query in dynamo")
    # add the created activity to this
    add_created_activity(company_id=company_id, query_id=query_id, user_id=user_id)
    print("added created activity")
    return response(200, parsed_query)


def handle_get(company_id, user_id):
    # Define the primary key for user's own queries
    primary_key_user = {
        "PK": f"COMPANY#{company_id}#USER#{user_id}",
        "SK": "QUERY#",
    }

    projection_expression = "SK, query_data.id, query_data.is_public, \
                            query_data.query_title, query_data.query_status, \
                            query_data.date_submitted"

    # Execute the query for user's own queries
    response_user = table.query(
        KeyConditionExpression=Key("PK").eq(primary_key_user["PK"])
        & Key("SK").begins_with(primary_key_user["SK"]),
        ProjectionExpression=projection_expression,
    )

    # Define the primary key for public queries
    primary_key_public = {
        "PK": f"COMPANY#{company_id}#PUBLIC",
        "SK": "QUERY#",
    }

    # Execute the query for public queries
    response_public = table.query(
        KeyConditionExpression=Key("PK").eq(primary_key_public["PK"])
        & Key("SK").begins_with(primary_key_public["SK"]),
        ProjectionExpression=projection_expression,
    )

    # Extract the items (queries) from the responses and de-duplicate
    items_priv = response_user.get("Items", [])
    items_public = response_public.get("Items", [])

    report_ids = set([item["SK"] for item in items_priv])
    items_public = [item for item in items_public if item["SK"] not in report_ids]

    all_items = items_priv + items_public

    res = [item["query_data"] for item in all_items]

    return response(200, res)
