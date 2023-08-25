import os
import json
import boto3

from boto3.dynamodb.conditions import Key


# Create the DynamoDB client
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["USERS_TABLE_NAME"])


def response(status_code, body={}):
    if type(body) == str:
        body = {"data": body}
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
    company_id = event["requestContext"]["authorizer"]["company_id"]
    user_id = event["pathParameters"]["user_id"]
    is_admin = event["requestContext"]["authorizer"]["role"].lower() == "admin"

    if not is_admin:
        return response(403, "Admins only.")

    if event["httpMethod"] == "PUT":
        data = json.loads(event.get("body", {}))
        return handle_put(company_id, user_id, data)

    if event["httpMethod"] == "DELETE":
        return handle_delete(company_id, user_id)

    return response(200)


def handle_put(company_id, user_id, data):
    primary_key = {
        "GSI1PK": f"COMPANY#{company_id}",
        "GSI1SK": f"USER#{user_id}",
    }
    res = table.query(
        IndexName="GSI1",
        KeyConditionExpression=Key("GSI1PK").eq(primary_key["GSI1PK"])
        & Key("GSI1SK").begins_with(primary_key["GSI1SK"]),
    )
    if not res.get("Items"):
        return response(403, "User Not found OR not allowed to do this action")

    update_expressions = []
    expression_attribute_values = {}
    expression_attribute_names = {}

    for key, value in data.items():
        # Use a substitution for the attribute name
        substituted_key = f"#{key}"
        expression_attribute_names[substituted_key] = key
        update_expressions.append(f"{substituted_key} = :{key}")
        expression_attribute_values[f":{key}"] = value
    update_expression = "SET " + ", ".join(update_expressions)

    primary_key = {
        "PK": f"USER#{user_id}",
    }

    # Making the update call
    res = table.update_item(
        Key=primary_key,
        UpdateExpression=update_expression,
        ExpressionAttributeValues=expression_attribute_values,
        ExpressionAttributeNames=expression_attribute_names,
    )

    print(res)
    # Checking if the update was successful
    if res.get("ResponseMetadata", {}).get("HTTPStatusCode") == 200:
        return response(200, "Updated successfully.")
    else:
        return response(500, "Error occurred during deletion.")


def handle_delete(company_id, user_id):
    primary_key = {
        "GSI1PK": f"COMPANY#{company_id}",
        "GSI1SK": f"USER#{user_id}",
    }
    res = table.query(
        IndexName="GSI1",
        KeyConditionExpression=Key("GSI1PK").eq(primary_key["GSI1PK"])
        & Key("GSI1SK").begins_with(primary_key["GSI1SK"]),
    )
    if not res.get("Items"):
        return response(403, "User Not found OR not allowed to do this action")

    primary_key = {
        "PK": f"USER#{user_id}",
    }

    # Making the delete call
    res = table.delete_item(Key=primary_key)

    print(res)

    # Checking if the deletion was successful
    if res.get("ResponseMetadata", {}).get("HTTPStatusCode") == 200:
        return response(200, "Deleted successfully.")
    else:
        return response(500, "Error occurred during deletion.")
