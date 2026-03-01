"""Tests for core/auth.py."""

import hashlib
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

    def test_falls_back_to_hostname_when_machine_id_missing(self, tmp_path):
        with patch("trivyal_agent.core.auth.Path") as mock_path_cls:
            fake_path = mock_path_cls.return_value
            fake_path.exists.return_value = False
            result = get_machine_fingerprint()
        expected = hashlib.sha256(socket.gethostname().encode()).hexdigest()
        assert result == expected

    def test_uses_machine_id_when_available(self, tmp_path):
        machine_id_file = tmp_path / "machine-id"
        machine_id_file.write_text("test-machine-id-123\n")
        with patch("trivyal_agent.core.auth.Path") as mock_path_cls:
            fake_path = mock_path_cls.return_value
            fake_path.exists.return_value = True
            fake_path.read_text.return_value = "test-machine-id-123\n"
            result = get_machine_fingerprint()
        expected = hashlib.sha256(b"test-machine-id-123").hexdigest()
        assert result == expected


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
