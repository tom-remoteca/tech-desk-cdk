#!/usr/bin/env python3

import aws_cdk as cdk

from stacks.api_stack import APIStack
from stacks.core_stack import CoreStack
from stacks.invite_stack import InviteStack
from stacks.endpoints_stack import EndpointsStack

config = {
    "DOMAIN_NAME": "techdeskportal.com",
    "CERTIFICATE_ARN": "arn:aws:acm:us-east-1:322517305488:certificate/6e7d609c-5c3f-4302-b74a-a54d97f38227",
    "HOSTED_ZONE_ID": "Z01294372TT7NF7CVNVDI",
    "AMPLIFY_GIT_OWNER": "tom-remoteca",
    "AMPLIFY_GIT_REPO": "tech-desk-app",
    "AMPLIFY_GIT_TOKEN_LOCATION": "git-token",
    "AMPLIFY_BRANCH": "main",
    "CLOUDFRONT_PUB_KEY": """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAupm1/KTtMiRiQZqk+Mgu
//8wylvxLL2RHHW3SrKK9RFxmrDJWRtY8K/aK0hugd0UoN1Wo64V9Gwi7At2ZTTO
OtVq5ckuwGtCW/qqTTOL4iNG+9myZ4DRoM+unwSwQI7FdYAhYaXEtGHzwKSBRZHE
sMoONDu90Mv/ztJ+FFajdXLABb7vHqqBydxUpsy39zgi/QZjPrVCgj3AwB5q9d6S
8DqqwQhyDpC1UziYPG4cdWjFVfTVcigB+TBlKVE7Nc9HOWNvVYc6PujHfRxFC7ff
RkFmgftyQE2r4sfa8uxAQzlXY5ZutzeAtdRwdrILnWZ2o71p7CVleFo+tpSBO/wg
9QIDAQAB
-----END PUBLIC KEY-----""",
}


app = cdk.App()
core_stack = CoreStack(app, "CoreStack", config=config)
api_stack = APIStack(
    app,
    "APIStack",
    config=config,
    hosted_zone=core_stack.hosted_zone,
    certificate=core_stack.certificate,
)
InviteStack(
    app,
    "InviteStack",
    api=api_stack.api,
    api_authorizer=api_stack.api_authorizer,
)
EndpointsStack(
    app,
    "EndpointsStack",
    api=api_stack.api,
    api_authorizer=api_stack.api_authorizer,
    next_auth_table=core_stack.next_auth_table,
    users_table=core_stack.users_table,
    core_table=core_stack.table,
    core_bucket=core_stack.bucket,
    activity_topic=core_stack.activity_topic,
    signed_url_generator=core_stack.signed_url_generator,
)
app.synth()
