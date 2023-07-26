import json
from typing import Any
from Crypto.Protocol.KDF import HKDF  # pip install pycryptodome
from Crypto.Hash import SHA256
from jose import jwe  # pip install python-jose


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
    '''
    Get the JWE payload from a NextAuth.js JWT/JWE token in Python

    Steps:
    1. Get the encryption key using HKDF defined in RFC5869
    2. Decrypt the JWE token using the encryption key
    3. Create a JSON object from the decrypted JWE token
    '''
    # Retrieve the same JWT_SECRET which was used to encrypt the JWE token on the NextAuth Server
    encryption_key = getDerivedEncryptionKey(SECRET)
    payload_str = jwe.decrypt(token, encryption_key).decode()
    payload: dict[str, Any] = json.loads(payload_str)

    return payload


SECRET = "qwertyuiopasdfgklzxcvbnmqwertyuioazfghjklxcvbnm"
TOKEN = "eyJhbGciOiJkaXIiLCJlbmMiOiJBMjU2R0NNIn0..GPpINi4FU902BNL8.oKer1rK9wfFhWdpuZyv40VUcLnK6QzBnIeOmQE4prSsDytFe2e7XuU6LuTHngzXWNp6qnyGls163pv2W-4gCBlpB4QunMHMLWz7aPnLxYWnSyc31s3zA_2EheVfMyCPzWxdWepEj5dKF9H_hGBjfj8_G1PLS5xURSLftjrRTZOX1qVMpH1BtBRX3VC18b1YAbxwcg_tus7PC__WEFimOrHi0fA8HKRN6aUXEgPsKZ73X-tNtnzVUZtWXm0yvTUh-Qe_vG179jsfjwho1DBYYd8vEXOmAPFb2On9KS050mEKY2hnBI9M-YZiCKV-HxUiBZBe2JYGGocUGpe1sYEVu1msqklcVDlxeZzmD53QWGybhOzDQ7uDbsXHGQsbGt3X6eQO3v_ITs9HM2ObknZtPkO3aZEOlLZyj0x3arxAO4zMnkd6jsy1sl2hBqWzH47w04ntFyaNvFuXH-uoucNNvaT7t8LX6ivjHs5UO_WiCG-m19aY.dIIZ_Yhw6ue0IW6LB8UyLg"
de = get_token(TOKEN)
print(de)
