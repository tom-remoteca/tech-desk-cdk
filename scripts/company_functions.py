import time
import uuid
import json
from boto3.dynamodb.conditions import Key
from datetime import datetime, timedelta


from mgmt_session import core_table, invite_table, users_table


def get_all_companies():
    res = core_table.query(
        IndexName="GSI1",
        KeyConditionExpression=Key("GSI1PK").eq("COMPANY")
        & Key("GSI1SK").begins_with("COMPANY#"),
    )
    return [{"name": i["name"], "id": i["id"]} for i in res.get("Items", [])]


def create_company(company_name):
    company_id = f"company_{str(uuid.uuid4())}"
    company_details = {"id": company_id, "name": company_name}
    res = core_table.put_item(
        Item={
            "PK": f"COMPANY#{company_id}",
            "SK": f"COMPANY#{company_id}",
            "GSI1PK": "COMPANY",
            "GSI1SK": f"COMPANY#{company_id}",
            **company_details,
        }
    )
    print(json.dumps(res, indent=4))
    print(f"Company '{company_name}' has been created id: {company_id}")


def create_invite_link(company_id, company_name):
    # Generate a UUID
    invite_token = str(uuid.uuid4())

    # Calculate the expiration time
    expiration_time = int((datetime.now() + timedelta(days=1)).timestamp())

    # Create the item
    item = {
        "inviteToken": invite_token,
        "company_id": company_id,
        "company_name": company_name,
        "expiration_time": expiration_time,
    }
    invite_table.put_item(Item=item)
    print(item)
    print(
        f'https://www.techdeskportal.com/auth/register?inviteToken={item["inviteToken"]}'
    )


def list_users(company_id):
    primary_key = {
        "GSI1PK": f"COMPANY#{company_id}",
        "GSI1SK": f"USER#",
    }

    # Execute the query for public queries
    res = users_table.query(
        IndexName="GSI1",  # replace with your GSI name
        KeyConditionExpression=Key("GSI1PK").eq(primary_key["GSI1PK"])
        & Key("GSI1SK").begins_with(primary_key["GSI1SK"]),
        ProjectionExpression="#N, image, email, #R, #I",  # email
        ExpressionAttributeNames={"#N": "name", "#R": "role", "#I": "id"},
    )
    users = res.get("Items", [])
    for user in users:
        print(f"{user['email']} - {user['name']}")
    # print(json.dumps(users, indent=4))


def delete_company(company_id):
    print(f"Company '{company_id}' has been deleted.")


def get_company_info(company_id):
    print(f"Company info for {company_id}:")


def delete_user(company_id, user_id):
    print(f"Company {company_id}, User '{user_id}' has been deleted.")
