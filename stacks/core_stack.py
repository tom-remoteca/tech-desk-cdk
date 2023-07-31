from aws_cdk import aws_s3 as s3
from aws_cdk import aws_iam as iam
from aws_cdk import aws_dynamodb as dynamodb
from aws_cdk import CfnOutput, Stack


class CoreStack(Stack):
    def __init__(
        self,
        scope: Stack,
        id: str,
        config: dict,
        # user_pool,
        **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)

        bucket = s3.Bucket(
            self,
            "Bucket",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
        )
        self.bucket = bucket

        ####### Core Table ##########
        table = dynamodb.Table(
            self,
            "CoreTable",
            partition_key=dynamodb.Attribute(
                name="PK", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="SK", type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
        )
        table.add_global_secondary_index(
            index_name="GSI1",
            partition_key=dynamodb.Attribute(
                name="GSI1PK", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="GSI1SK", type=dynamodb.AttributeType.STRING
            ),
        )
        self.table = table

        # Users Table
        users_table = dynamodb.Table(
            self,
            "UsersTable",
            table_name="users-table",
            partition_key=dynamodb.Attribute(
                name="PK", type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
        )

        ####### Next Auth Table ##########
        next_auth_table = dynamodb.Table(
            scope=self,
            id="NextAuthTable",
            table_name="next-auth",
            partition_key=dynamodb.Attribute(
                name="pk", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="sk", type=dynamodb.AttributeType.STRING
            ),
            time_to_live_attribute="expires",
        )
        # Add a global secondary index to the table
        next_auth_table.add_global_secondary_index(
            index_name="GSI1",
            partition_key=dynamodb.Attribute(
                name="GSI1PK", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="GSI1SK", type=dynamodb.AttributeType.STRING
            ),
        )
        self.next_auth_table = next_auth_table
        # Output the access key details
        CfnOutput(self, "NextAuthTableName", value=next_auth_table.table_name)
        # Create an IAM user
        next_auth_user = iam.User(
            self, "NextAuthUser2", user_name="next-auth-user-2"
        )

        # Attach DynamoDB read/write permissions to the user
        dynamodb_policy = iam.PolicyStatement(
            actions=["dynamodb:*"], resources=[next_auth_table.table_arn]
        )
        next_auth_user.add_to_policy(dynamodb_policy)

        # Create an access key for the user
        access_key = iam.CfnAccessKey(
            self, "NextAuthUserAccessKey", user_name=next_auth_user.user_name
        )

        # Output the access key details
        CfnOutput(self, "NextAuthUserAccessKeyId", value=access_key.ref)
        CfnOutput(
            self,
            "NextAuthUserSecretAccessKey",
            value=access_key.attr_secret_access_key,
        )

        ####### Amplify ######

        # Create Amplify App, using the above repo as the code source.
        # amplify_app = amplify.App(
        #     self,
        #     "TechDesk App",
        #     source_code_provider=amplify.GitHubSourceCodeProvider(
        #         owner=config['AMPLIFY_GIT_OWNER'],
        #         repository=config['AMPLIFY_GIT_REPO'],
        #         oauth_token=SecretValue.secrets_manager(
        #             config['AMPLIFY_GIT_TOKEN_LOCATION']
        #         ),
        #     ),
        # )

        # cfn_amplify_app = amplify_app.node.default_child
        # cfn_amplify_app.platform = 'WEB_COMPUTE'
        # cfn_amplify_app.framework = "Next.js - SSR"

        # amplify_app.add_custom_rule(
        #     amplify.CustomRule.SINGLE_PAGE_APPLICATION_REDIRECT)

        # mainBranch = amplify_app.add_branch(config['AMPLIFY_BRANCH'])
        # cfn_amplify_branch = mainBranch.node.default_child
        # cfn_amplify_branch.framework = "Next.js - SSR"

        # domain = amplify_app.add_domain(config['DOMAIN_NAME'])
        # domain.map_root(mainBranch),
        # domain.map_sub_domain(mainBranch, "www")
