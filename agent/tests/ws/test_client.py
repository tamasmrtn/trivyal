"""Tests for ws/client.py."""

import json
from base64 import b64encode
from unittest.mock import AsyncMock, patch

import pytest
from nacl.signing import SigningKey
from trivyal_agent.config import Settings
from trivyal_agent.ws.client import AgentClient, AuthError


def _make_settings(**overrides) -> Settings:
    signing_key = SigningKey.generate()
    pub_b64 = b64encode(signing_key.verify_key.encode()).decode()
    defaults = {
        "hub_url": "ws://localhost:8099",
        "token": "test-token",
        "key": pub_b64,
        "scan_schedule": "0 2 * * *",
        "data_dir": "/tmp/trivyal-test",
        "heartbeat_interval": 30,
        "reconnect_delay": 1,
    }
    defaults.update(overrides)
    return Settings(**defaults)


def _make_challenge_message(signing_key: SigningKey) -> str:
    challenge = bytes(32)  # all zeros for testing
    signature = signing_key.sign(challenge).signature
    return json.dumps(
        {
            "type": "challenge",
            "challenge": challenge.hex(),
            "signature": signature.hex(),
        }
    )


class TestAgentClientHandshake:
    async def test_raises_auth_error_on_wrong_message_type(self):
        settings = _make_settings()
        client = AgentClient(settings)

        mock_ws = AsyncMock()
        mock_ws.recv = AsyncMock(return_value=json.dumps({"type": "unexpected"}))

        with pytest.raises(AuthError, match="Expected challenge message"):
            await client._handshake(mock_ws)

    async def test_raises_auth_error_on_invalid_signature(self):
        signing_key = SigningKey.generate()
        pub_b64 = b64encode(signing_key.verify_key.encode()).decode()
        settings = _make_settings(key=pub_b64)
        client = AgentClient(settings)

        # Sign with a DIFFERENT key than what the settings has
        wrong_key = SigningKey.generate()
        challenge = bytes(32)
        bad_sig = wrong_key.sign(challenge).signature

        mock_ws = AsyncMock()
        mock_ws.recv = AsyncMock(
            return_value=json.dumps(
                {
                    "type": "challenge",
                    "challenge": challenge.hex(),
                    "signature": bad_sig.hex(),
                }
            )
        )

        with pytest.raises(AuthError, match="signature verification failed"):
            await client._handshake(mock_ws)

    async def test_handshake_sends_fingerprint_and_metadata(self, tmp_path):
        signing_key = SigningKey.generate()
        pub_b64 = b64encode(signing_key.verify_key.encode()).decode()
        settings = _make_settings(key=pub_b64, data_dir=str(tmp_path))
        client = AgentClient(settings)

        challenge_msg = _make_challenge_message(signing_key)
        sent_messages = []

        mock_ws = AsyncMock()
        mock_ws.recv = AsyncMock(return_value=challenge_msg)
        mock_ws.send = AsyncMock(side_effect=lambda m: sent_messages.append(json.loads(m)))

        with (
            patch("trivyal_agent.ws.client.collect_host_metadata", return_value={"hostname": "testhost"}),
            patch("trivyal_agent.ws.client.list_cached", return_value=[]),
        ):
            await client._handshake(mock_ws)

        types_sent = [m["type"] for m in sent_messages]
        assert "fingerprint" in types_sent
        assert "host_metadata" in types_sent

        fingerprint_msg = next(m for m in sent_messages if m["type"] == "fingerprint")
        assert len(fingerprint_msg["fingerprint"]) == 64  # sha256 hex

        metadata_msg = next(m for m in sent_messages if m["type"] == "host_metadata")
        assert metadata_msg["metadata"]["hostname"] == "testhost"


class TestAgentClientScanCycle:
    async def test_sends_scan_results_to_hub(self, tmp_path):
        settings = _make_settings(data_dir=str(tmp_path))
        client = AgentClient(settings)

        mock_ws = AsyncMock()
        sent = []
        mock_ws.send = AsyncMock(side_effect=lambda m: sent.append(json.loads(m)))

        scan_result = {"ArtifactName": "nginx:latest", "Results": []}
        containers = [{"image_name": "nginx:latest", "container_name": "my-nginx"}]

        with (
            patch("trivyal_agent.ws.client.list_running_images", return_value=containers),
            patch("trivyal_agent.ws.client.scan_all_images", return_value=[scan_result]),
            patch("trivyal_agent.ws.client.save"),
        ):
            await client._run_scan_cycle(mock_ws)

        assert len(sent) == 1
        assert sent[0]["type"] == "scan_result"
        assert sent[0]["data"]["ArtifactName"] == "nginx:latest"
        assert sent[0]["container_name"] == "my-nginx"

    async def test_does_nothing_when_no_containers(self, tmp_path):
        settings = _make_settings(data_dir=str(tmp_path))
        client = AgentClient(settings)

        mock_ws = AsyncMock()

        with patch("trivyal_agent.ws.client.list_running_images", return_value=[]):
            await client._run_scan_cycle(mock_ws)

        mock_ws.send.assert_not_called()

    async def test_handles_list_containers_failure_gracefully(self, tmp_path):
        settings = _make_settings(data_dir=str(tmp_path))
        client = AgentClient(settings)

        mock_ws = AsyncMock()

        with patch("trivyal_agent.ws.client.list_running_images", side_effect=Exception("docker down")):
            # Should not raise
            await client._run_scan_cycle(mock_ws)

        mock_ws.send.assert_not_called()
