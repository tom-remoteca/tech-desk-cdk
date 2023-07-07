#!/usr/bin/env python3

import aws_cdk as cdk

from cdk_td_app.cdk_td_app_stack import CdkTdAppStack


app = cdk.App()
CdkTdAppStack(app, "cdk-td-app")

app.synth()
