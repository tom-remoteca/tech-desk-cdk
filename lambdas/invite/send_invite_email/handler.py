import json
import os
import boto3
import uuid
from botocore.exceptions import ClientError
from datetime import datetime, timedelta

# Create the DynamoDB client
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["INVITE_TABLE_NAME"])

# Create the SES client
ses_client = boto3.client("ses")


def send_email(recipient, link, company_name, invitor):
    try:
        response = ses_client.send_email(
            Source='"TechDesk" <noreply@techdeskportal.com>',
            Destination={"ToAddresses": [recipient]},
            Message={
                "Subject": {"Data": "You've been invited to TechDesk"},
                "Body": {
                    "Text": {"Data": f"Here is your invite link: {link}"},
                    "Html": {
                        "Data": """
                        <!DOCTYPE html>

                        <html lang='en' xmlns:o='urn:schemas-microsoft-com:office:office' xmlns:v='urn:schemas-microsoft-com:vml'>
                        <head>
                        <title></title>
                        <meta content='text/html; charset=utf-8' http-equiv='Content-Type'/>
                        <meta content='width=device-width, initial-scale=1.0' name='viewport'/>
                        <style>
                                * {{
                                    box-sizing: border-box;
                                }}

                                body {{
                                    margin: 0;
                                    padding: 0;
                                }}

                                a[x-apple-data-detectors] {{
                                    color: inherit !important;
                                    text-decoration: inherit !important;
                                }}

                                #MessageViewBody a {{
                                    color: inherit;
                                    text-decoration: none;
                                }}

                                p {{
                                    line-height: inherit
                                }}

                                .desktop_hide,
                                .desktop_hide table {{
                                    mso-hide: all;
                                    display: none;
                                    max-height: 0px;
                                    overflow: hidden;
                                }}

                                .image_block img+div {{
                                    display: none;
                                }}

                                @media (max-width:520px) {{
                                    .desktop_hide table.icons-inner {{
                                        display: inline-block !important;
                                    }}

                                    .icons-inner {{
                                        text-align: center;
                                    }}

                                    .icons-inner td {{
                                        margin: 0 auto;
                                    }}

                                    .mobile_hide {{
                                        display: none;
                                    }}

                                    .row-content {{
                                        width: 100% !important;
                                    }}

                                    .stack .column {{
                                        width: 100%;
                                        display: block;
                                    }}

                                    .mobile_hide {{
                                        min-height: 0;
                                        max-height: 0;
                                        max-width: 0;
                                        overflow: hidden;
                                        font-size: 0px;
                                    }}

                                    .desktop_hide,
                                    .desktop_hide table {{
                                        display: table !important;
                                        max-height: none !important;
                                    }}

                                    .row-1 .column-1 .block-2.heading_block h1 {{
                                        font-size: 24px !important;
                                    }}
                                }}
                            </style>
                        </head>
                        <body style='background-color: #fff; margin: 0; padding: 0; -webkit-text-size-adjust: none; text-size-adjust: none;'>
                        <table border='0' cellpadding='0' cellspacing='0' class='nl-container' role='presentation' style='mso-table-lspace: 0pt; mso-table-rspace: 0pt; background-color: #fff;' width='100%'>
                        <tbody>
                        <tr>
                        <td>
                        <table align='center' border='0' cellpadding='0' cellspacing='0' class='row row-1' role='presentation' style='mso-table-lspace: 0pt; mso-table-rspace: 0pt;' width='100%'>
                        <tbody>
                        <tr>
                        <td>
                        <table align='center' border='0' cellpadding='0' cellspacing='0' class='row-content stack' role='presentation' style='mso-table-lspace: 0pt; mso-table-rspace: 0pt; color: #000; width: 500px; margin: 0 auto;' width='500'>
                        <tbody>
                        <tr>
                        <td class='column column-1' style='mso-table-lspace: 0pt; mso-table-rspace: 0pt; font-weight: 400; text-align: left; padding-bottom: 5px; padding-top: 5px; vertical-align: top; border-top: 0px; border-right: 0px; border-bottom: 0px; border-left: 0px;' width='100%'>
                        <table border='0' cellpadding='10' cellspacing='0' class='image_block block-1' role='presentation' style='mso-table-lspace: 0pt; mso-table-rspace: 0pt;' width='100%'>
                        <tr>
                        <td class='pad'>
                        <div align='center' class='alignment' style='line-height:10px'><img src='https://www.techdeskportal.com/images/TechDeskLogo.png' style='display: block; height: auto; border: 0; max-width: 225px; width: 100%;' width='225'/></div>
                        </td>
                        </tr>
                        </table>
                        <table border='0' cellpadding='10' cellspacing='0' class='heading_block block-2' role='presentation' style='mso-table-lspace: 0pt; mso-table-rspace: 0pt;' width='100%'>
                        <tr>
                        <td class='pad'>
                        <h1 style='margin: 0; color: #000000; direction: ltr; font-family: 'Open Sans', 'Helvetica Neue', Helvetica, Arial, sans-serif; font-size: 27px; font-weight: 700; letter-spacing: normal; line-height: 150%; text-align: center; margin-top: 0; margin-bottom: 0;'><span class='tinyMce-placeholder'>Welcome To TechDesk</span></h1>
                        </td>
                        </tr>
                        </table>
                        <table border='0' cellpadding='10' cellspacing='0' class='paragraph_block block-3' role='presentation' style='mso-table-lspace: 0pt; mso-table-rspace: 0pt; word-break: break-word;' width='100%'>
                        <tr>
                        <td class='pad'>
                        <div style='color:#000000;direction:ltr;font-family:Arial, 'Helvetica Neue', Helvetica, sans-serif;font-size:18px;font-weight:400;letter-spacing:0px;line-height:150%;text-align:center;mso-line-height-alt:27px;'>
                        <p style='margin: 0;'>You have been invited to join <b>{company}</b> on TechDesk by {invitor}. Please click the sign up link below to create your account.</p>
                        </div>
                        </td>
                        </tr>
                        </table>
                        <table border='0' cellpadding='10' cellspacing='0' class='image_block block-4' role='presentation' style='mso-table-lspace: 0pt; mso-table-rspace: 0pt;' width='100%'>
                        <tr>
                        <td class='pad'>
                        <div align='center' class='alignment' style='line-height:10px'><img src='https://www.techdeskportal.com/images/TechDeskRender.jpg' style='display: block; height: auto; border: 0; max-width: 500px; width: 100%;' width='500'/></div>
                        </td>
                        </tr>
                        </table>
                        </td>
                        </tr>
                        </tbody>
                        </table>
                        </td>
                        </tr>
                        </tbody>
                        </table>
                        <table border='0' cellpadding='15' cellspacing='0' class='button_block block-1' role='presentation' style='mso-table-lspace: 0pt; mso-table-rspace: 0pt;' width='100%'>
                            <tr>
                                <td class='pad'>
                                    <div align='center' class='alignment'>
                                        <a href='{invite_link}' style='text-decoration: none; display: inline-block; color: #ffffff; background-color: #233dff; border-radius: 10px; width: auto; border-top: 0px solid transparent; font-weight: 400; border-right: 0px solid transparent; border-bottom: 0px solid transparent; border-left: 0px solid transparent; padding-top: 15px; padding-bottom: 15px; font-family: Arial, "Helvetica Neue", Helvetica, sans-serif; font-size: 20px; text-align: center; mso-border-alt: none; word-break: keep-all; width: 80%; max-width: 300px;' target='_blank'>
                                            <span style='padding-left: 25px; padding-right: 25px; font-size: 20px; display: inline-block; letter-spacing: normal;'>
                                                <span style='word-break: break-word; line-height: 36px;'>Sign Up</span>
                                            </span>
                                        </a>
                                    </div>
                                </td>
                            </tr>
                        </table>
                        </td>
                        </tr>
                        </tbody>
                        </table>
                        </td>
                        </tr>
                        </tbody>
                        </table>
                        </body>
                        </html>
                        """.format(
                            company=company_name, invitor=invitor, invite_link=link
                        )
                    },
                },
            },
        )
        return response
    except ClientError as e:
        print(e.response["Error"]["Message"])
        return None


def response(status_code, body={}):
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
    company_name = event["requestContext"]["authorizer"]["company_name"]
    invitor = event["requestContext"]["authorizer"]["name"]

    email = event["queryStringParameters"].get("email")
    if not email:
        return response(401, "Missing email.")

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

    try:
        # Put the item into DynamoDB
        table.put_item(Item=item)
    except ClientError as e:
        print(e.response["Error"]["Message"])
        return response(500, "Error inserting item into DynamoDB")

    # Send the email
    link = f"https://www.techdeskportal.com/auth/register?inviteToken={invite_token}"

    send_email(email, link, company_name, invitor)

    return response(200, item)
