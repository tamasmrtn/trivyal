"""Token generation, hashing, verification, and Ed25519 key management."""

import hashlib
import hmac
import secrets
from base64 import b64decode, b64encode

from nacl.signing import SigningKey, VerifyKey

TOKEN_BYTES = 32


def generate_token() -> str:
    return secrets.token_urlsafe(TOKEN_BYTES)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def verify_token(token: str, token_hash: str) -> bool:
    candidate = hashlib.sha256(token.encode()).hexdigest()
    return hmac.compare_digest(candidate, token_hash)


def generate_keypair() -> tuple[str, str]:
    """Generate an Ed25519 keypair. Returns (public_key_b64, private_key_b64)."""
    signing_key = SigningKey.generate()
    verify_key = signing_key.verify_key
    return (
        b64encode(verify_key.encode()).decode(),
        b64encode(signing_key.encode()).decode(),
    )


def sign_challenge(private_key_b64: str, challenge: bytes) -> bytes:
    """Sign a challenge with the hub's private key."""
    signing_key = SigningKey(b64decode(private_key_b64))
    return signing_key.sign(challenge).signature


def verify_signature(public_key_b64: str, signature: bytes, challenge: bytes) -> bool:
    """Verify a signature against the hub's public key."""
    try:
        verify_key = VerifyKey(b64decode(public_key_b64))
        verify_key.verify(challenge, signature)
        return True
    except Exception:
        return False


def generate_admin_token(secret_key: str) -> str:
    """Derive a deterministic admin API token from the secret key."""
    return hashlib.sha256(f"admin:{secret_key}".encode()).hexdigest()
