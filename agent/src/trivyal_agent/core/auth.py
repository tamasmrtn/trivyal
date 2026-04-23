"""Fingerprint generation and Ed25519 signature verification."""

import hashlib
import os
import platform
import socket
from base64 import b64decode
from pathlib import Path

from nacl.signing import VerifyKey

# Known-bad DMI UUID that some VMs report (not unique).
_BAD_DMI_UUIDS = {"03000200-0400-0500-0006-000700080009"}


def _read_file(path: str) -> str | None:
    """Read a file and return stripped contents, or None on any error."""
    try:
        text = Path(path).read_text().strip()
        return text if text else None
    except Exception:
        return None


def get_machine_fingerprint(data_dir: Path | None = None) -> str:
    """Return a stable SHA-256 hash of the machine's unique ID.

    Sources tried in order:
    1. Persisted fingerprint file ({data_dir}/fingerprint) for stability.
    2. /etc/machine-id
    3. /sys/class/dmi/id/product_uuid (reject known-bad UUIDs)
    4. Composite: hostname + cpu_count + platform.machine()

    The result is persisted to disk after first computation.
    """
    # 1. Check persisted fingerprint
    if data_dir:
        fp_file = data_dir / "fingerprint"
        try:
            stored = fp_file.read_text().strip()
            if stored:
                return stored
        except Exception:  # nosec B110
            pass

    # 2. Try /etc/machine-id
    machine_id = _read_file("/etc/machine-id")

    # 3. Try DMI product UUID
    if not machine_id:
        dmi_uuid = _read_file("/sys/class/dmi/id/product_uuid")
        if dmi_uuid and dmi_uuid.lower() not in _BAD_DMI_UUIDS:
            machine_id = dmi_uuid

    # 4. Composite fallback
    if not machine_id:
        machine_id = f"{socket.gethostname()}:{os.cpu_count()}:{platform.machine()}"

    fingerprint = hashlib.sha256(machine_id.encode()).hexdigest()

    # Persist for stability across restarts
    if data_dir:
        try:
            fp_file = data_dir / "fingerprint"
            fp_file.write_text(fingerprint)
        except Exception:  # nosec B110
            pass

    return fingerprint


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
