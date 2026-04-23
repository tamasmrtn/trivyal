"""Tests for core/auth.py."""

import hashlib
import os
import platform
import socket
from base64 import b64encode
from unittest.mock import patch

import pytest
from nacl.signing import SigningKey
from trivyal_agent.core.auth import get_machine_fingerprint, verify_hub_signature


class TestGetMachineFingerprint:
    def test_returns_hex_string(self):
        fp = get_machine_fingerprint()
        assert isinstance(fp, str)
        assert len(fp) == 64  # sha256 hex digest is 64 chars
        int(fp, 16)  # raises ValueError if not valid hex

    def test_deterministic(self):
        assert get_machine_fingerprint() == get_machine_fingerprint()

    def test_persisted_fingerprint_takes_priority(self, tmp_path):
        fp_file = tmp_path / "fingerprint"
        fp_file.write_text("a" * 64)

        result = get_machine_fingerprint(data_dir=tmp_path)

        assert result == "a" * 64

    def test_uses_machine_id_when_available(self, tmp_path):
        with patch("trivyal_agent.core.auth._read_file") as mock_read:
            mock_read.side_effect = lambda p: "test-machine-id-123" if "machine-id" in p else None
            result = get_machine_fingerprint(data_dir=tmp_path)

        expected = hashlib.sha256(b"test-machine-id-123").hexdigest()
        assert result == expected

    def test_tries_dmi_uuid_when_machine_id_missing(self, tmp_path):
        with patch("trivyal_agent.core.auth._read_file") as mock_read:
            mock_read.side_effect = lambda p: "valid-dmi-uuid-here" if "dmi" in p else None
            result = get_machine_fingerprint(data_dir=tmp_path)

        expected = hashlib.sha256(b"valid-dmi-uuid-here").hexdigest()
        assert result == expected

    def test_rejects_known_bad_dmi_uuid(self, tmp_path):
        with patch("trivyal_agent.core.auth._read_file") as mock_read:
            mock_read.side_effect = lambda p: "03000200-0400-0500-0006-000700080009" if "dmi" in p else None
            result = get_machine_fingerprint(data_dir=tmp_path)

        # Should fall back to composite, not use the bad UUID
        composite = f"{socket.gethostname()}:{os.cpu_count()}:{platform.machine()}"
        expected = hashlib.sha256(composite.encode()).hexdigest()
        assert result == expected

    def test_composite_fallback_uses_multiple_factors(self, tmp_path):
        with patch("trivyal_agent.core.auth._read_file", return_value=None):
            result = get_machine_fingerprint(data_dir=tmp_path)

        composite = f"{socket.gethostname()}:{os.cpu_count()}:{platform.machine()}"
        expected = hashlib.sha256(composite.encode()).hexdigest()
        assert result == expected

    def test_persists_newly_computed_fingerprint(self, tmp_path):
        with patch("trivyal_agent.core.auth._read_file", return_value=None):
            result = get_machine_fingerprint(data_dir=tmp_path)

        fp_file = tmp_path / "fingerprint"
        assert fp_file.exists()
        assert fp_file.read_text() == result

    def test_works_without_data_dir(self):
        result = get_machine_fingerprint(data_dir=None)
        assert isinstance(result, str)
        assert len(result) == 64


class TestVerifyHubSignature:
    @pytest.fixture
    def keypair(self):
        """Generate a fresh Ed25519 keypair for testing."""
        signing_key = SigningKey.generate()
        verify_key = signing_key.verify_key
        pub_b64 = b64encode(verify_key.encode()).decode()
        return signing_key, pub_b64

    def test_valid_signature_returns_true(self, keypair):
        signing_key, pub_b64 = keypair
        challenge = b"hello-challenge"
        signature = signing_key.sign(challenge).signature
        assert verify_hub_signature(pub_b64, signature.hex(), challenge.hex()) is True

    def test_wrong_signature_returns_false(self, keypair):
        _, pub_b64 = keypair
        challenge = b"hello-challenge"
        bad_sig = b"\x00" * 64
        assert verify_hub_signature(pub_b64, bad_sig.hex(), challenge.hex()) is False

    def test_wrong_public_key_returns_false(self, keypair):
        signing_key, _ = keypair
        other_key = SigningKey.generate()
        wrong_pub_b64 = b64encode(other_key.verify_key.encode()).decode()
        challenge = b"hello-challenge"
        signature = signing_key.sign(challenge).signature
        assert verify_hub_signature(wrong_pub_b64, signature.hex(), challenge.hex()) is False

    def test_tampered_challenge_returns_false(self, keypair):
        signing_key, pub_b64 = keypair
        challenge = b"hello-challenge"
        signature = signing_key.sign(challenge).signature
        tampered = b"tampered-challenge"
        assert verify_hub_signature(pub_b64, signature.hex(), tampered.hex()) is False

    def test_invalid_public_key_returns_false(self):
        assert verify_hub_signature("not-valid-b64!!!", "aa" * 64, "bb" * 16) is False
