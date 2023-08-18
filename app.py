#!/usr/bin/env python3

import aws_cdk as cdk

from stacks.api_stack import APIStack
from stacks.core_stack import CoreStack
from stacks.invite_stack import InviteStack
from stacks.endpoints_stack import EndpointsStack

config = {
    "DOMAIN_NAME": "techdeskportal.com",
    "HOSTED_ZONE_ID": "Z01294372TT7NF7CVNVDI",
    "AMPLIFY_GIT_OWNER": "tom-remoteca",
    "AMPLIFY_GIT_REPO": "tech-desk-app",
    "AMPLIFY_GIT_TOKEN_LOCATION": "git-token",
    "AMPLIFY_BRANCH": "main",
}

app = cdk.App()
core_stack = CoreStack(app, "CoreStack", config=config)
api_stack = APIStack(app, "APIStack", config=config)
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
    core_table=core_stack.table,
    core_bucket=core_stack.bucket,
)
app.synth()
