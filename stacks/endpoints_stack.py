from aws_cdk import aws_sns as sns
from aws_cdk import aws_sns_subscriptions as subscriptions
from aws_cdk import aws_dynamodb as dynamodb
from aws_cdk import aws_lambda as _lambda
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_apigateway as apigateway
from aws_cdk import CfnOutput, Stack, SecretValue, Duration
from constructs import Construct

import os


class EndpointsStack(Stack):
    def __init__(
        self,
        scope: Stack,
        id: str,
        api,
        api_authorizer,
        next_auth_table: dynamodb.Table,
        users_table: dynamodb.Table,
        core_table: dynamodb.Table,
        core_bucket: s3.Bucket,
        activity_topic: sns.Topic,
        signed_url_generator: _lambda.Function,
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

        get_ai_query_lambda = _lambda.Function(
            self,
            "GetAIQueryLambda",
            handler="handler.handler",
            runtime=_lambda.Runtime.PYTHON_3_7,
            code=_lambda.Code.from_asset(
                f"{os.path.dirname(__file__)}/../lambdas/app_endpoints/ai/get_ai_query"
            ),
            environment={
                "CORE_TABLE_NAME": core_table.table_name,
            },
            timeout=Duration.seconds(60),
        )
        core_table.grant_read_data(get_ai_query_lambda)

        queries_lambda = _lambda.Function(
            self,
            "QueriesLambda",
            handler="handler.handler",
            runtime=_lambda.Runtime.PYTHON_3_7,
            code=_lambda.Code.from_asset(
                f"{os.path.dirname(__file__)}/../lambdas/app_endpoints/queries/queries"
            ),
            environment={
                "CORE_TABLE_NAME": core_table.table_name,
                "BUCKET_NAME": core_bucket.bucket_name,
                "ACTIVITY_TOPIC": activity_topic.topic_arn,
            },
        )
        activity_topic.grant_publish(queries_lambda)
        core_table.grant_read_write_data(queries_lambda)
        next_auth_table.grant_read_data(queries_lambda)
        core_bucket.grant_put(queries_lambda)

        query_lambda = _lambda.Function(
            self,
            "QueryLambda",
            handler="handler.handler",
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset(
                f"{os.path.dirname(__file__)}/../lambdas/app_endpoints/queries/query"
            ),
            timeout=Duration.seconds(10),
            environment={
                "CORE_TABLE_NAME": core_table.table_name,
                "BUCKET_NAME": core_bucket.bucket_name,
                "SIGNED_URL_GENERATOR_FUNCTION_NAME": signed_url_generator.function_name,
            },
        )
        core_table.grant_read_write_data(query_lambda)
        signed_url_generator.grant_invoke(query_lambda)

        notifications_lambda = _lambda.Function(
            self,
            "NotificationsLambda",
            handler="handler.handler",
            runtime=_lambda.Runtime.PYTHON_3_7,
            code=_lambda.Code.from_asset(
                f"{os.path.dirname(__file__)}/../lambdas/app_endpoints/notifications/notifications"
            ),
            environment={
                "CORE_TABLE_NAME": core_table.table_name,
            },
        )
        core_table.grant_read_data(notifications_lambda)

        notification_lambda = _lambda.Function(
            self,
            "NotificationLambda",
            handler="handler.handler",
            runtime=_lambda.Runtime.PYTHON_3_7,
            code=_lambda.Code.from_asset(
                f"{os.path.dirname(__file__)}/../lambdas/app_endpoints/notifications/notification"
            ),
            environment={
                "CORE_TABLE_NAME": core_table.table_name,
            },
        )
        core_table.grant_write_data(notification_lambda)

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

        activity_lambda = _lambda.Function(
            self,
            "ActivityLambda",
            handler="handler.handler",
            runtime=_lambda.Runtime.PYTHON_3_7,
            code=_lambda.Code.from_asset(
                f"{os.path.dirname(__file__)}/../lambdas/app_endpoints/activity"
            ),
            environment={"CORE_TABLE_NAME": core_table.table_name},
        )
        core_table.grant_read_write_data(activity_lambda)
        activity_topic.add_subscription(
            subscriptions.LambdaSubscription(activity_lambda)
        )

        reports_lambda = _lambda.Function(
            self,
            "ReportsLambda",
            handler="handler.handler",
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset(
                f"{os.path.dirname(__file__)}/../lambdas/app_endpoints/reports/reports"
            ),
            environment={
                "CORE_TABLE_NAME": core_table.table_name,
            },
        )
        core_table.grant_read_write_data(reports_lambda)

        ai_api = api.root.add_resource("ai")
        ai_query = ai_api.add_resource("new_query")
        ai_history = ai_api.add_resource("history")
        ai_query_history = ai_history.add_resource("{ai_query_id}")

        queries_api = api.root.add_resource("queries")
        query_api = queries_api.add_resource("{query_id}")
        activity_api = query_api.add_resource("activity")

        reports_api = api.root.add_resource("reports")

        users_api = api.root.add_resource("users")
        user_api = users_api.add_resource("{user_id}")

        notifications_api = api.root.add_resource("notifications")
        notification_api = notifications_api.add_resource("{notification_id}")

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

        ai_query_history.add_method(
            "GET",
            apigateway.LambdaIntegration(get_ai_query_lambda),
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

        notifications_api.add_method(
            "GET",
            apigateway.LambdaIntegration(notifications_lambda),
            authorizer=api_authorizer,
        )

        notification_api.add_method(
            "DELETE",
            apigateway.LambdaIntegration(notification_lambda),
            authorizer=api_authorizer,
        )

        activity_api.add_method(
            "GET",
            apigateway.LambdaIntegration(activity_lambda),
            authorizer=api_authorizer,
        )

        activity_api.add_method(
            "POST",
            apigateway.LambdaIntegration(activity_lambda),
            authorizer=api_authorizer,
        )

        reports_api.add_method(
            "GET",
            apigateway.LambdaIntegration(reports_lambda),
            authorizer=api_authorizer,
        )
