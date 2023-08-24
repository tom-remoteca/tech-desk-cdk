from aws_cdk import aws_lambda as _lambda
from aws_cdk import aws_apigateway as apigateway

from constructs import Construct
from aws_cdk import CfnOutput, Stack, SecretValue, Duration

import os


class EndpointsStack(Stack):
    def __init__(
        self,
        scope: Stack,
        id: str,
        api,
        api_authorizer,
        next_auth_table,
        users_table,
        core_table,
        core_bucket,
        **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)

        ai_query_lambda = _lambda.Function(
            self,
            "AIQueryLambda",
            handler="handler.handler",
            runtime=_lambda.Runtime.PYTHON_3_7,
            code=_lambda.Code.from_asset(
                f"{os.path.dirname(__file__)}/../lambdas/app_endpoints/ai/new_query"
            ),
            environment={
                "CORE_TABLE_NAME": core_table.table_name,
            },
            timeout=Duration.seconds(60),
        )
        core_table.grant_read_write_data(ai_query_lambda)

        ai_history_lambda = _lambda.Function(
            self,
            "AIHistoryLambda",
            handler="handler.handler",
            runtime=_lambda.Runtime.PYTHON_3_7,
            code=_lambda.Code.from_asset(
                f"{os.path.dirname(__file__)}/../lambdas/app_endpoints/ai/history"
            ),
            environment={
                "CORE_TABLE_NAME": core_table.table_name,
            },
            timeout=Duration.seconds(60),
        )
        core_table.grant_read_write_data(ai_history_lambda)

        queries_lambda = _lambda.Function(
            self,
            "QueriesLambda",
            handler="handler.handler",
            runtime=_lambda.Runtime.PYTHON_3_7,
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

        users_lambda = _lambda.Function(
            self,
            "UsersLambda",
            handler="handler.handler",
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset(
                f"{os.path.dirname(__file__)}/../lambdas/app_endpoints/user_mgmt/users"
            ),
            environment={"USERS_TABLE_NAME": users_table.table_name},
        )
        users_table.grant_read_data(users_lambda)

        user_lambda = _lambda.Function(
            self,
            "UserLambda",
            handler="handler.handler",
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset(
                f"{os.path.dirname(__file__)}/../lambdas/app_endpoints/user_mgmt/user"
            ),
            environment={"USERS_TABLE_NAME": users_table.table_name},
        )
        users_table.grant_read_write_data(user_lambda)

        ai_api = api.root.add_resource("ai")
        ai_query = ai_api.add_resource("new_query")
        ai_history = ai_api.add_resource("history")
        queries_api = api.root.add_resource("queries")
        query_api = queries_api.add_resource("{query_id}")
        users_api = api.root.add_resource("users")
        user_api = users_api.add_resource("{user_id}")
        # activity_api = query_api.add_resource("activity")

        ai_query.add_method(
            "POST",
            apigateway.LambdaIntegration(ai_query_lambda),
            authorizer=api_authorizer,
        )

        ai_history.add_method(
            "GET",
            apigateway.LambdaIntegration(ai_history_lambda),
            authorizer=api_authorizer,
        )

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

        users_api.add_method(
            "GET",
            apigateway.LambdaIntegration(users_lambda),
            authorizer=api_authorizer,
        )

        user_api.add_method(
            "PUT",
            apigateway.LambdaIntegration(user_lambda),
            authorizer=api_authorizer,
        )

        user_api.add_method(
            "DELETE",
            apigateway.LambdaIntegration(user_lambda),
            authorizer=api_authorizer,
        )
