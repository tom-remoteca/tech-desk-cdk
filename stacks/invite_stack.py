from aws_cdk import aws_lambda as _lambda
from aws_cdk import aws_dynamodb as dynamodb
from aws_cdk import aws_apigateway as apigateway

from constructs import Construct
from aws_cdk import CfnOutput, Stack, SecretValue

import os


class InviteStack(Stack):
    def __init__(
        self,
        scope: Stack,
        id: str,
        api,
        api_authorizer,
        **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)

        # DynamoDB table
        invite_table = dynamodb.Table(
            self,
            "InviteLinks",
            partition_key=dynamodb.Attribute(
                name="inviteToken", type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            time_to_live_attribute="expiration_time",
        )

        # Lookup Lambda function
        lookup_lambda = _lambda.Function(
            self,
            "InviteLookupLambda",
            handler="handler.handler",
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset(
                f"{os.path.dirname(__file__)}/../lambdas/invite/lookup_lambda"
            ),
            environment={
                "INVITE_TABLE_NAME": invite_table.table_name,
            },
        )

        # Grant the lambda function read access to the DynamoDB table
        invite_table.grant_read_data(lookup_lambda)

        # create_token_lambda Lambda function
        create_token_lambda = _lambda.Function(
            self,
            "InviteCreateLambda",
            handler="handler.handler",
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset(
                f"{os.path.dirname(__file__)}/../lambdas/invite/create_token_lambda"
            ),
            environment={
                "INVITE_TABLE_NAME": invite_table.table_name,
            },
        )

        invite_table.grant_read_write_data(create_token_lambda)

        contact_us_lambda = _lambda.Function(
            self,
            "ContactUsLambda",
            handler="handler.handler",
            runtime=_lambda.Runtime.PYTHON_3_7,
            code=_lambda.Code.from_asset(
                f"{os.path.dirname(__file__)}/../lambdas/app_endpoints/contact_us"
            ),
        )

        invite_api = api.root.add_resource("invite")
        lookup_invite_api = invite_api.add_resource("lookup")
        create_invite_api = invite_api.add_resource("create")
        contact_api = api.root.add_resource("contact")

        lookup_invite_api.add_method(
            "GET",
            apigateway.LambdaIntegration(lookup_lambda),
        )

        create_invite_api.add_method(
            "GET",
            apigateway.LambdaIntegration(create_token_lambda),
            authorizer=api_authorizer,
        )

        contact_api.add_method(
            "POST", apigateway.LambdaIntegration(contact_us_lambda)
        )
