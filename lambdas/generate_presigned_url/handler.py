import os
import rsa
import boto3
import base64
from botocore.exceptions import ClientError
from botocore.signers import CloudFrontSigner
from datetime import datetime, timedelta, timezone

# Secrets to fetch from AWS Security Manager
KEY_PRIVATE_KEY = "SIGNING-PRIVATE-KEY"
KEY_KEY_ID = os.environ["KEY_KEY_ID"]
CUSTOM_DOMAIN = os.environ["CUSTOM_DOMAIN"]


def get_secret(secret_key):
    # This code is straight from the AWS console code example except it returns the secret value
    session = boto3.session.Session()
    client = session.client(service_name="secretsmanager")
    get_secret_value_response = client.get_secret_value(SecretId=secret_key)
    if "SecretString" in get_secret_value_response:
        secret = get_secret_value_response["SecretString"]
    else:
        secret = base64.b64decode(get_secret_value_response["SecretBinary"])
    return secret


def rsa_signer(message):
    private_key = get_secret(KEY_PRIVATE_KEY)
    return rsa.sign(
        message, rsa.PrivateKey.load_pkcs1(private_key.encode("utf8")), "SHA-1"
    )  # CloudFront requires SHA-1 hash


def sign_url(url_to_sign):
    key_id = KEY_KEY_ID
    cf_signer = CloudFrontSigner(key_id, rsa_signer)
    signed_url = cf_signer.generate_presigned_url(
        url=url_to_sign,
        date_less_than=datetime.now(timezone.utc) + timedelta(hours=1),
    )
    return signed_url


def handler(event, context):
    print(event)
    key = event.get("key", None)
    if key:
        url_to_sign = f"{CUSTOM_DOMAIN}/{key}"
        return {"signed_url": sign_url(url_to_sign)}

    keys = event.get("keys", [])
    if keys:
        res = {}
        for k in keys:
            url_to_sign = f"{CUSTOM_DOMAIN}/{k}"
            res[k] = {"signed_url": sign_url(url_to_sign)}
        print(res)
        return res
