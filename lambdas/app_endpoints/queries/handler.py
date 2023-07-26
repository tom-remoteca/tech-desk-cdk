import os
import cgi
import json
import uuid
import boto3
import base64
from io import BytesIO

from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError


# Create the DynamoDB client
dynamodb = boto3.resource("dynamodb")
auth_table = dynamodb.Table('next-auth')
table = dynamodb.Table(os.environ["CORE_TABLE_NAME"])

BUCKET_NAME = os.environ["BUCKET_NAME"]


def auth(auth_header):
    # Extract token from "Bearer td_tok"
    td_tok = auth_header.split(" ")[1]

    # Decode the base64 string
    decoded_td_tok = base64.b64decode(td_tok).decode('utf-8')

    # Split the string on " "
    user_id, tenant_id, session_token = decoded_td_tok.split(" ")
    print(user_id, tenant_id, session_token)
    res = auth_table.query(
        KeyConditionExpression=Key('PK').eq(f"USER#{user_id}") & Key(
            'SK').begins_with(f"ACCOUNT#")
    )
    auth = res.get("Items", [])
    print(auth)
    return user_id, tenant_id


def write_file_to_s3(query_id, file_data):
    # print(file_data)
    # Initialize Boto3 S3 client
    s3_client = boto3.client('s3')

    attachment_id = f"attachment_{uuid.uuid4()}"

    file_key = f"queries/{query_id}/{attachment_id}"

    # Write the file to S3 bucket
    s3_client.upload_fileobj(file_data['file_data_bytes'], BUCKET_NAME, file_key, ExtraArgs={
                             'ContentType': file_data['content_type']})
    return attachment_id, file_key
    # s3_client.put_object(Bucket=BUCKET_NAME, Key=f'2-{file_key}', Body=file_data['file_data_bytes'])


def parse_raw_query(query_id, event):
    # Decode base64 encoded data from the event
    encoded_data = event['body']
    decoded_data = base64.b64decode(encoded_data)

    # Parse the content type and boundary from the 'Content-Type' header
    content_type_header = event['headers']['content-type']
    content_type, options = cgi.parse_header(content_type_header)
    boundary = options.get('boundary')

    # Create a BytesIO object to use as the file pointer
    fp = BytesIO(decoded_data)

    # Create a FieldStorage object to parse the multipart form data
    fs = cgi.FieldStorage(fp=fp, headers=event['headers'], environ={
                          'REQUEST_METHOD': 'POST'}, keep_blank_values=True)

    # Dictionary to store the parsed form data
    form_data = {}

    # Iterate through each field in the multipart form data
    for field in fs.list:
        if field.filename:  # This is a file field
            form_data[field.name] = {
                'file_name': field.filename,
                'content_type': field.type,
                'file_data': field.file,  # Read the file data here
                'file_data_bytes': BytesIO(field.file.read())
            }
        else:  # This is a regular form field
            form_data[field.name] = field.value
    print(form_data.keys())

    out = {}
    attachments = []
    out['query_id'] = query_id
    for k, v in form_data.items():
        if k.startswith("file-"):
            attachment_id, file_key = write_file_to_s3(
                query_id=query_id, file_data=v)
            attachments.append({
                "file_name": v['file_name'],
                "attachment_id": attachment_id,
                "file_key": file_key
            })
            continue
        elif k == "usecase_tags":
            raw_tags = json.loads(v)
            tags = [obj['value'] for obj in raw_tags]
            out['usecase_tags'] = tags
        else:
            out[k] = v
    out['attachments'] = attachments
    return out


def response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "OPTIONS,POST,GET",
        },
        "body": json.dumps(body)
    }


def handler(event, context):
    user_id, tenant_id = auth(event['headers']['Authorization'])
    print(user_id, tenantid)
    print(event)
    return response(200, {"message": "successs"})
    company_id = event.get("company_id", "company_EXAMPLE")
    user_id = event.get("user_id", "user_EXAMPLE")

    if event["httpMethod"] == "GET":
        return handle_get(company_id, user_id, event)
    if event["httpMethod"] == "POST":
        return handle_post(company_id, user_id, event)
    return 200


def handle_post(company_id, user_id, event):
    query_id = f"query_{uuid.uuid4()}"
    print(query_id)

    parsed_query = parse_raw_query(query_id, event)
    print(parsed_query)

    return response(200, parsed_query)


def handle_get(company_id, user_id, event):
    res = table.query(
        KeyConditionExpression=Key('PK').eq(f"COMPANY#{company_id}#QUERY") & Key(
            'SK').begins_with(f"MEO#{user_id}#QUERY#")
    )
    queries = res.get("Items", [])
    res = table.query(
        KeyConditionExpression=Key('PK').eq(f"COMPANY#{company_id}#QUERY") & Key(
            'SK').begins_with(f"MEO#FALSE#QUERY#")
    )
    queries.append(res.get("Items", []))
    return [i['query'] for i in res.get('Items', [])]
