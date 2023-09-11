import os
import time
import json
from typing import Any
from Cryptodome.Protocol.KDF import HKDF  # pip install pycryptodome
from Cryptodome.Hash import SHA256
from jose import jwe  # pip install python-jose

SECRET = "qwertyuiopasdfgklzxcvbnmqwertyuioazfghjklxcvbnm"


def getDerivedEncryptionKey(secret: str) -> Any:
    # Think about including the context in your environment variables.
    context = str.encode("NextAuth.js Generated Encryption Key")
    return HKDF(
        master=secret.encode(),
        key_len=32,
        salt="".encode(),
        hashmod=SHA256,
        num_keys=1,
        context=context,
    )


def get_token(token: str) -> dict[str, Any]:
    """
    Get the JWE payload from a NextAuth.js JWT/JWE token in Python

    Steps:
    1. Get the encryption key using HKDF defined in RFC5869
    2. Decrypt the JWE token using the encryption key
    3. Create a JSON object from the decrypted JWE token
    """
    # Retrieve the same JWT_SECRET which was used to encrypt the JWE token on the NextAuth Server
    encryption_key = getDerivedEncryptionKey(SECRET)
    payload_str = jwe.decrypt(token, encryption_key).decode()
    payload: dict[str, Any] = json.loads(payload_str)

    return payload


def handler(event, context):
    region = os.environ.get("REGION")
    account_id = os.environ.get("ACCOUNT_ID")
    api_id = os.environ.get("API_ID")
    stage = os.environ.get("STAGE")
    method_arn = f"arn:aws:execute-api:{region}:{account_id}:{api_id}/{stage}/*/*"
    print(method_arn)
    print(event)
    token = event["authorizationToken"]
    # method_arn = event["methodArn"]
    jwt = token.split(" ")[1]

    try:
        parsed_token = get_token(jwt)
    except Exception as e:
        # Invalid JWT, deny access.
        print("INVALID TOKEN")
        return generate_policy(token, "Deny", method_arn)

    if parsed_token["exp"] < int(time.time()):
        # Token has expired, deny access
        print("EXPIRED TOKEN")
        return generate_policy(token, "Deny", method_arn)
    print("ALLOWED!")
    return generate_policy(token, "Allow", method_arn, parsed_token)


def generate_policy(principal_id, effect, resource, parsed_token={}):
    return {
        "principalId": principal_id,
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {"Action": "execute-api:Invoke", "Effect": effect, "Resource": resource}
            ],
        },
        "context": parsed_token,
    }
