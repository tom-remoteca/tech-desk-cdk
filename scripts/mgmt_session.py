import boto3


# For a Boto3 client.
boto3.setup_default_session(profile_name="td-prod")

dynamodb = boto3.resource("dynamodb")
core_table = dynamodb.Table("CoreStack-CoreTable97EB8292-OSGHIVMEFPBR")
users_table = dynamodb.Table("users-table")
invite_table = dynamodb.Table("InviteStack-InviteLinks9ADBED25-FSLCEVMX5O3C")


def publish_to_sns(message):
    sns = boto3.client("sns")

    # Publish a message to the specified SNS topic
    response = sns.publish(
        TopicArn="arn:aws:sns:eu-west-2:322517305488:CoreStack-ActivityTopic0E625C11-VNjvUNnYn3NR",
        Message=message,
    )
    print(response)

    return response
