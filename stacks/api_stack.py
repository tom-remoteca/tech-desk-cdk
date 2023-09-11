from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda as _lambda
from aws_cdk import aws_route53 as route53
from aws_cdk import aws_dynamodb as dynamodb
from aws_cdk import aws_apigateway as apigateway
from aws_cdk import aws_certificatemanager as acm
from aws_cdk import aws_route53_targets as targets
from aws_cdk import aws_logs as logs
from constructs import Construct
from aws_cdk import (
    CfnOutput,
    Stack,
    SecretValue,
    BundlingOptions,
    DockerImage,
)

import aws_cdk.aws_amplify_alpha as amplify

import os


class APIStack(Stack):
    def __init__(
        self,
        scope: Stack,
        id: str,
        config: dict,
        **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)

        hosted_zone = route53.HostedZone.from_hosted_zone_attributes(
            self,
            "HostedZone",
            zone_name=config["DOMAIN_NAME"],
            hosted_zone_id=config["HOSTED_ZONE_ID"],
        )

        certificate = acm.Certificate(
            self,
            "Certificate",
            domain_name=config["DOMAIN_NAME"],
            subject_alternative_names=[f"*.{config['DOMAIN_NAME']}"],
            validation=acm.CertificateValidation.from_dns(hosted_zone),
        )

        # log_role = iam.Role(
        #     self,
        #     "ApiGatewayLoggingRole",
        #     assumed_by=iam.ServicePrincipal("apigateway.amazonaws.com"),
        # )

        # log_role.add_managed_policy(
        #     iam.ManagedPolicy.from_aws_managed_policy_name(
        #         "service-role/AmazonAPIGatewayPushToCloudWatchLogs"
        #     )
        # )
        # account = apigateway.CfnAccount(
        #     self, "ApiGatewayAccount", cloud_watch_role_arn=log_role.role_arn
        # )

        api = apigateway.RestApi(
            self,
            "backend-api",
            domain_name=apigateway.DomainNameOptions(
                domain_name=f"api.{config['DOMAIN_NAME']}",
                certificate=certificate,
            ),
            binary_media_types=["multipart/form-data"],
            default_cors_preflight_options=apigateway.CorsOptions(
                allow_origins=apigateway.Cors.ALL_ORIGINS,
                allow_methods=apigateway.Cors.ALL_METHODS,
                allow_headers=apigateway.Cors.DEFAULT_HEADERS,
                allow_credentials=True,
            ),
            # deploy_options=apigateway.StageOptions(
            #     access_log_destination=apigateway.LogGroupLogDestination(
            #         log_group=logs.LogGroup(self, "ApiGatewayLogs")
            #     ),
            #     logging_level=apigateway.MethodLoggingLevel.INFO,
            #     data_trace_enabled=True,
            #     # tracing_enabled=True,
            # ),
        )
        # api.node.add_dependency(account)
        api.rest_api_root_resource_id
        api.rest_api_id
        self.api = api
        route53.ARecord(
            self,
            "APICustomDomainAliasRecord",
            record_name=f"api.{config['DOMAIN_NAME']}",
            zone=hosted_zone,
            target=route53.RecordTarget.from_alias(targets.ApiGateway(api)),
        )

        custom_authorizer_lambda = _lambda.Function(
            self,
            "CustomAuthorizerFunction",
            handler="handler.handler",
            runtime=_lambda.Runtime.PYTHON_3_9,
            environment={
                "REGION": self.region,
                "ACCOUNT_ID": self.account,
                "API_ID": api.rest_api_id,
                "STAGE": "prod",
            },
            code=_lambda.Code.from_asset(
                f"{os.path.dirname(__file__)}/../lambdas/authorizer",
                bundling=BundlingOptions(
                    # image=_lambda.Runtime.PYTHON_3_9.bundling_image,
                    image=DockerImage.from_registry(
                        "amazon/aws-sam-cli-build-image-python3.9"
                    ),
                    command=[
                        "bash",
                        "-c",
                        "pip install --no-cache -r requirements.txt -t /asset-output && cp -au . /asset-output",
                    ],
                ),
            ),
        )

        self.api_authorizer = apigateway.TokenAuthorizer(
            self,
            "MyAuthorizer",
            handler=custom_authorizer_lambda,
            identity_source=apigateway.IdentitySource.header("Authorization"),
        )

        # self.api_auth = apigateway.CognitoUserPoolsAuthorizer(
        #     self, "apiAuthoriser", cognito_user_pools=[user_pool]
        # )
        # self.api_auth_type = apigateway.AuthorizationType.COGNITO
        # CfnOutput(self, "apiEndpoint", value=self.api.url)
