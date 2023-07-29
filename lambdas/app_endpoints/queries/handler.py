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


def create_query_dynamo(company_id, user_id, query_id, query_data):
    if query_data['my_eyes_only']:
        is_public = "TRUE"
    else:
        is_public = "FALSE"
    
    query_data['id'] = query_id
    query_data['date_submitted'] = str(time.time())
    query_data['query_status'] = "Submitted"
    query_data['company_id'] = company_id

    res = table.put_item(
        Item={
            'PK': f"COMPANY#{company_id}#USER#{user_id}",
            'SK': f"QUERY#{query_id}",
            'GSI1PK': f"COMPANY#{company_id}",
            'GSI1SK': f"PUBLIC#{is_public}QUERY#{query_id}",
            'query_data': query_data
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
        "body": json.dumps(body, default=str)
    }


def handler(event, context):
    print(event)
    user_id = event['requestContext']['authorizer']['sub']
    company_id = event['requestContext']['authorizer']['tenant_id']

    if event["httpMethod"] == "GET":
        return handle_get(company_id, user_id, event)
        
    if event["httpMethod"] == "POST":
        return handle_post(company_id, user_id, event)
    return 200


def handle_post(company_id, user_id, event):
    query_id = f"query_{uuid.uuid4()}"
    print(query_id)

    # Process data in webkit form and save attachments to s3
    parsed_query = parse_raw_query(query_id, event)
    
    # Save this request to Dynamo
    create_query_dynamo(company_id, user_id, query_id, parsed_query)

    return response(200, parsed_query)


def handle_get(company_id, user_id, event):
    # Define the primary key for user's own queries
    primary_key_user = {
        'PK': f'COMPANY#{company_id}#USER#{user_id}',
    }

    projection_expression = 'SK, query_data.id, query_data.my_eyes_only, query_data.query_title, query_data.query_status, query_data.date_submitted'

    # Execute the query for user's own queries
    response_user = table.query(
        KeyConditionExpression=boto3.dynamodb.conditions.Key('PK').eq(primary_key_user['PK']),
        ProjectionExpression=projection_expression,

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
