import os
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_iam as iam
from aws_cdk import aws_dynamodb as dynamodb
from aws_cdk import aws_route53 as route53
from aws_cdk import CfnOutput, Stack
from aws_cdk import aws_sns as sns
from aws_cdk import aws_certificatemanager as acm
from aws_cdk import aws_cloudfront as cloudfront
from aws_cdk import aws_cloudfront_origins as origins
from aws_cdk import aws_lambda as _lambda
from aws_cdk import Stack, Duration, Environment


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
            cors=[
                s3.CorsRule(
                    allowed_methods=[s3.HttpMethods.GET],
                    allowed_origins=[
                        "http://localhost:3000",
                        "https://www.techdeskportal.com",
                    ],
                    allowed_headers=["*"],
                    max_age=3000,
                )
            ],
        )
        self.bucket = bucket

        ####### Core Table ##########
        table = dynamodb.Table(
            self,
            "CoreTable",
            partition_key=dynamodb.Attribute(
                name="PK", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(name="SK", type=dynamodb.AttributeType.STRING),
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
        users_table.add_global_secondary_index(
            index_name="GSI1",
            partition_key=dynamodb.Attribute(
                name="GSI1PK", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="GSI1SK", type=dynamodb.AttributeType.STRING
            ),
        )
        self.users_table = users_table

        ####### Next Auth Table ##########
        next_auth_table = dynamodb.Table(
            scope=self,
            id="NextAuthTable",
            table_name="next-auth",
            partition_key=dynamodb.Attribute(
                name="pk", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(name="sk", type=dynamodb.AttributeType.STRING),
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
        next_auth_user = iam.User(self, "NextAuthUser2", user_name="next-auth-user-2")

        # Attach DynamoDB read/write permissions to the user
        dynamodb_policy = iam.PolicyStatement(
            actions=["dynamodb:*"], resources=[next_auth_table.table_arn]
        )
        next_auth_user.add_to_policy(dynamodb_policy)

        # Create an access key for the user
        access_key = iam.CfnAccessKey(
            self, "NextAuthUserAccessKey", user_name=next_auth_user.user_name
        )

        activity_topic = sns.Topic(
            self, "Activity Topic", display_name="Activity Topic"
        )
        self.activity_topic = activity_topic

        # Output the access key details
        CfnOutput(self, "NextAuthUserAccessKeyId", value=access_key.ref)
        CfnOutput(
            self,
            "NextAuthUserSecretAccessKey",
            value=access_key.attr_secret_access_key,
        )

        hosted_zone = route53.HostedZone.from_hosted_zone_attributes(
            self,
            "HostedZone",
            zone_name=config["DOMAIN_NAME"],
            hosted_zone_id=config["HOSTED_ZONE_ID"],
        )
        self.hosted_zone = hosted_zone

        api_gw_cert = acm.Certificate(
            self,
            "ApiGwCertificate",
            domain_name=config["DOMAIN_NAME"],
            subject_alternative_names=[f"*.{config['DOMAIN_NAME']}"],
            validation=acm.CertificateValidation.from_dns(hosted_zone),
        )
        self.certificate = api_gw_cert

        cf_cert = acm.Certificate.from_certificate_arn(
            self, "CloudfrontCertificate", certificate_arn=config["CERTIFICATE_ARN"]
        )

        pub_key = cloudfront.PublicKey(
            self, "PublicKey", encoded_key=config["CLOUDFRONT_PUB_KEY"]
        )

        no_cache_policy = cloudfront.CachePolicy(
            self,
            "NoCachePolicy",
            cache_policy_name="NoCachePolicy",
            default_ttl=Duration.seconds(0),
            max_ttl=Duration.seconds(0),
            min_ttl=Duration.seconds(0),
            comment="Cache policy with no caching",
            header_behavior=cloudfront.CacheHeaderBehavior.none(),
            cookie_behavior=cloudfront.CacheCookieBehavior.none(),
            query_string_behavior=cloudfront.CacheQueryStringBehavior.none(),
            enable_accept_encoding_brotli=False,
            enable_accept_encoding_gzip=False,
        )

        oai = cloudfront.OriginAccessIdentity(self, "OAI")
        bucket.grant_read(oai)

        distribution = cloudfront.Distribution(
            self,
            "Distribution",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3Origin(bucket=bucket, origin_access_identity=oai),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                cache_policy=no_cache_policy,
                trusted_key_groups=[
                    cloudfront.KeyGroup(self, "signedKeyGroup", items=[pub_key])
                ],
                allowed_methods=cloudfront.AllowedMethods.ALLOW_GET_HEAD_OPTIONS,
                cached_methods=cloudfront.CachedMethods.CACHE_GET_HEAD,
            ),
            domain_names=[f"files.{config['DOMAIN_NAME']}"],
            certificate=cf_cert,
        )

        route53.CnameRecord(
            self,
            "CnameRecord",
            record_name="files",
            zone=hosted_zone,
            domain_name=distribution.distribution_domain_name,
        )

        generate_url_function = _lambda.Function(
            self,
            "GeneratePresignedUrlFunction",
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler="handler.handler",
            memory_size=512,
            code=_lambda.Code.from_asset(
                f"{os.path.dirname(__file__)}/../lambdas/generate_presigned_url"
            ),
            environment={
                "BUCKET_NAME": bucket.bucket_name,
                "CUSTOM_DOMAIN": f"https://files.{config['DOMAIN_NAME']}",
                "KEY_KEY_ID": pub_key.public_key_id,
            },
        )

        ssm_policy = iam.PolicyStatement(
            actions=["secretsmanager:GetSecretValue"],
            resources=[
                "arn:aws:secretsmanager:eu-west-2:322517305488:secret:SIGNING-PRIVATE-KEY-LFfOAS"
            ],
        )
        generate_url_function.role.add_to_policy(ssm_policy)

        # alias = _lambda.Alias(
        #     self,
        #     "Alias",
        #     alias_name="live",
        #     version=generate_url_function.current_version,
        #     provisioned_concurrent_executions=1,
        # )
        self.signed_url_generator = generate_url_function
