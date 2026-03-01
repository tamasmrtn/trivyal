"""Fingerprint generation and Ed25519 signature verification."""

import hashlib
import socket
from base64 import b64decode
from pathlib import Path

from nacl.signing import VerifyKey


def get_machine_fingerprint() -> str:
    """Return a stable SHA-256 hash of the machine's unique ID.

    Reads /etc/machine-id when available, falls back to hostname.
    """
    machine_id_path = Path("/etc/machine-id")
    machine_id = machine_id_path.read_text().strip() if machine_id_path.exists() else socket.gethostname()
    return hashlib.sha256(machine_id.encode()).hexdigest()


def verify_hub_signature(public_key_b64: str, signature_hex: str, challenge_hex: str) -> bool:
    """Verify that the hub signed the challenge with its private key.

    Args:
        public_key_b64: Hub's Ed25519 public key, base64-encoded.
        signature_hex: Hex-encoded signature bytes.
        challenge_hex: Hex-encoded challenge bytes.

    Returns:
        True if the signature is valid, False otherwise.
    """
    try:
        verify_key = VerifyKey(b64decode(public_key_b64))
        challenge = bytes.fromhex(challenge_hex)
        signature = bytes.fromhex(signature_hex)
        verify_key.verify(challenge, signature)
        return True
    except Exception:
        return False
