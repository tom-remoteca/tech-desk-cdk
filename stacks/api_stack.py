from aws_cdk import aws_lambda as _lambda
from aws_cdk import aws_route53 as route53
from aws_cdk import aws_apigateway as apigateway
from aws_cdk import aws_route53_targets as targets
from aws_cdk import aws_certificatemanager as acm
from aws_cdk import aws_cloudfront as cloudfront
from aws_cdk import aws_cloudfront_origins as origins
from aws_cdk import aws_s3 as s3

from aws_cdk import Stack, BundlingOptions, DockerImage, Duration


import os


class APIStack(Stack):
    def __init__(
        self,
        scope: Stack,
        id: str,
        config: dict,
        hosted_zone,
        certificate,
        **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)

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
        )

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
