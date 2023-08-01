from aws_cdk import aws_lambda as _lambda
from aws_cdk import aws_apigateway as apigateway

from constructs import Construct
from aws_cdk import CfnOutput, Stack, SecretValue

import os


class EndpointsStack(Stack):
    def __init__(
        self,
        scope: Stack,
        id: str,
        api,
        api_authorizer,
        next_auth_table,
        core_table,
        core_bucket,
        **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)

        queries_lambda = _lambda.Function(
            self,
            "QueriesLambda",
            handler="handler.handler",
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset(
                f"{os.path.dirname(__file__)}/../lambdas/app_endpoints/queries"
            ),
            environment={
                "CORE_TABLE_NAME": core_table.table_name,
                "BUCKET_NAME": core_bucket.bucket_name,
            },
        )

        core_table.grant_read_write_data(queries_lambda)
        next_auth_table.grant_read_data(queries_lambda)
        core_bucket.grant_put(queries_lambda)

        query_lambda = _lambda.Function(
            self,
            "QueryLambda",
            handler="handler.handler",
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset(
                f"{os.path.dirname(__file__)}/../lambdas/app_endpoints/query"
            ),
            environment={
                "CORE_TABLE_NAME": core_table.table_name,
                "BUCKET_NAME": core_bucket.bucket_name,
            },
        )

        core_table.grant_read_write_data(query_lambda)
        core_bucket.grant_put(query_lambda)

        queries_api = api.root.add_resource("queries")
        query_api = queries_api.add_resource("{query_id}")
        # activity_api = query_api.add_resource("activity")

        queries_api.add_method(
            "GET",
            apigateway.LambdaIntegration(queries_lambda),
            authorizer=api_authorizer,
        )

        queries_api.add_method(
            "POST",
            apigateway.LambdaIntegration(queries_lambda),
            authorizer=api_authorizer,
        )

        query_api.add_method(
            "GET",
            apigateway.LambdaIntegration(query_lambda),
            authorizer=api_authorizer,
        )
