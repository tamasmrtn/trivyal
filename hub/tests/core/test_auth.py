"""Tests for token and key management."""

from trivyal_hub.core.auth import (
    generate_admin_token,
    generate_keypair,
    generate_token,
    sign_challenge,
    verify_signature,
)


class TestTokenGeneration:
    def test_generates_url_safe_string(self):
        token = generate_token()
        assert len(token) > 0
        assert " " not in token

    def test_tokens_are_unique(self):
        assert generate_token() != generate_token()


class TestKeypair:
    def test_generates_valid_keypair(self):
        pub, priv = generate_keypair()
        assert len(pub) > 0
        assert len(priv) > 0
        assert pub != priv

    def test_sign_and_verify(self):
        pub, priv = generate_keypair()
        challenge = b"test-challenge-data"
        sig = sign_challenge(priv, challenge)
        assert verify_signature(pub, sig, challenge) is True

    def test_wrong_key_fails_verification(self):
        _, priv = generate_keypair()
        other_pub, _ = generate_keypair()
        challenge = b"test-challenge-data"
        sig = sign_challenge(priv, challenge)
        assert verify_signature(other_pub, sig, challenge) is False


class TestAdminToken:
    def test_deterministic(self):
        t1 = generate_admin_token("secret")
        t2 = generate_admin_token("secret")
        assert t1 == t2

    def test_different_secrets_differ(self):
        t1 = generate_admin_token("secret-a")
        t2 = generate_admin_token("secret-b")
        assert t1 != t2
