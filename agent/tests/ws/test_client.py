"""Tests for ws/client.py."""

import json
from base64 import b64encode
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from nacl.signing import SigningKey
from trivyal_agent.config import Settings
from trivyal_agent.health import HealthServer
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

    async def test_handshake_sets_health_connected(self, tmp_path):
        signing_key = SigningKey.generate()
        pub_b64 = b64encode(signing_key.verify_key.encode()).decode()
        settings = _make_settings(key=pub_b64, data_dir=str(tmp_path))
        health = MagicMock(spec=HealthServer)
        client = AgentClient(settings, health=health)

        challenge_msg = _make_challenge_message(signing_key)
        mock_ws = AsyncMock()
        mock_ws.recv = AsyncMock(return_value=challenge_msg)

        with (
            patch("trivyal_agent.ws.client.collect_host_metadata", return_value={}),
            patch("trivyal_agent.ws.client.list_cached", return_value=[]),
        ):
            await client._handshake(mock_ws)

        health.set_connected.assert_called_once_with(True)


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
            patch("trivyal_agent.ws.client.run_misconfig_checks", return_value=[]),
        ):
            await client._run_scan_cycle(mock_ws)

        assert len(sent) == 1
        assert sent[0]["type"] == "scan_result"
        assert sent[0]["data"]["ArtifactName"] == "nginx:latest"
        assert sent[0]["container_name"] == "my-nginx"

    async def test_sends_misconfig_results_to_hub(self, tmp_path):
        settings = _make_settings(data_dir=str(tmp_path))
        client = AgentClient(settings)

        mock_ws = AsyncMock()
        sent = []
        mock_ws.send = AsyncMock(side_effect=lambda m: sent.append(json.loads(m)))

        scan_result = {"ArtifactName": "nginx:latest", "Results": []}
        containers = [{"image_name": "nginx:latest", "container_name": "my-nginx"}]
        misconfig_result = {
            "container_id": "abc123",
            "container_name": "my-nginx",
            "image_name": "nginx:latest",
            "findings": [
                {
                    "check_id": "PRIV_001",
                    "severity": "HIGH",
                    "title": "Privileged",
                    "fix_guideline": "Fix it",
                }
            ],
        }

        with (
            patch("trivyal_agent.ws.client.list_running_images", return_value=containers),
            patch("trivyal_agent.ws.client.scan_all_images", return_value=[scan_result]),
            patch("trivyal_agent.ws.client.save"),
            patch("trivyal_agent.ws.client.run_misconfig_checks", return_value=[misconfig_result]),
        ):
            await client._run_scan_cycle(mock_ws)

        types = [m["type"] for m in sent]
        assert "scan_result" in types
        assert "misconfig_result" in types
        misconfig_msg = next(m for m in sent if m["type"] == "misconfig_result")
        assert misconfig_msg["data"]["container_id"] == "abc123"

    async def test_does_nothing_when_no_containers(self, tmp_path):
        settings = _make_settings(data_dir=str(tmp_path))
        client = AgentClient(settings)

        mock_ws = AsyncMock()

        with (
            patch("trivyal_agent.ws.client.list_running_images", return_value=[]),
            patch("trivyal_agent.ws.client.run_misconfig_checks", return_value=[]),
        ):
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


class TestScanCycleDigestSkip:
    async def test_skips_image_when_digest_matches_cache(self, tmp_path):
        from trivyal_agent.core.cache import save

        settings = _make_settings(data_dir=str(tmp_path))
        client = AgentClient(settings)

        # Pre-populate cache with a known digest
        save(tmp_path, "nginx:latest", {"ArtifactName": "nginx:latest"}, image_digest="sha256:abc")

        mock_ws = AsyncMock()
        # Container reports the same digest that is in the cache
        containers = [{"image_name": "nginx:latest", "container_name": "my-nginx", "image_digest": "sha256:abc"}]

        with (
            patch("trivyal_agent.ws.client.list_running_images", return_value=containers),
            patch("trivyal_agent.ws.client.scan_all_images", return_value=[]) as mock_scan,
            patch("trivyal_agent.ws.client.run_misconfig_checks", return_value=[]),
        ):
            await client._run_scan_cycle(mock_ws)

        # scan_all_images is never reached when all images are skipped
        mock_scan.assert_not_called()
        mock_ws.send.assert_not_called()

    async def test_scans_image_when_digest_differs_from_cache(self, tmp_path):
        from trivyal_agent.core.cache import save

        settings = _make_settings(data_dir=str(tmp_path))
        client = AgentClient(settings)

        # Cache holds an old digest
        save(tmp_path, "nginx:latest", {"ArtifactName": "nginx:latest"}, image_digest="sha256:old")

        mock_ws = AsyncMock()
        sent = []
        mock_ws.send = AsyncMock(side_effect=lambda m: sent.append(json.loads(m)))

        scan_result = {"ArtifactName": "nginx:latest", "Results": []}
        # Container now reports a newer digest
        containers = [{"image_name": "nginx:latest", "container_name": "my-nginx", "image_digest": "sha256:new"}]

        with (
            patch("trivyal_agent.ws.client.list_running_images", return_value=containers),
            patch("trivyal_agent.ws.client.scan_all_images", return_value=[scan_result]) as mock_scan,
            patch("trivyal_agent.ws.client.save"),
            patch("trivyal_agent.ws.client.run_misconfig_checks", return_value=[]),
        ):
            await client._run_scan_cycle(mock_ws)

        mock_scan.assert_called_once_with(["nginx:latest"])
        assert any(m["type"] == "scan_result" for m in sent)

    async def test_scans_image_when_no_cache_entry_exists(self, tmp_path):
        settings = _make_settings(data_dir=str(tmp_path))
        client = AgentClient(settings)

        mock_ws = AsyncMock()
        sent = []
        mock_ws.send = AsyncMock(side_effect=lambda m: sent.append(json.loads(m)))

        scan_result = {"ArtifactName": "redis:7", "Results": []}
        containers = [{"image_name": "redis:7", "container_name": "my-redis", "image_digest": "sha256:aabbcc"}]

        with (
            patch("trivyal_agent.ws.client.list_running_images", return_value=containers),
            patch("trivyal_agent.ws.client.scan_all_images", return_value=[scan_result]) as mock_scan,
            patch("trivyal_agent.ws.client.save"),
            patch("trivyal_agent.ws.client.run_misconfig_checks", return_value=[]),
        ):
            await client._run_scan_cycle(mock_ws)

        mock_scan.assert_called_once_with(["redis:7"])

    async def test_scans_image_when_digest_is_empty(self, tmp_path):
        """An empty digest (inspect failed) is never treated as a match — always scan."""
        from trivyal_agent.core.cache import save

        settings = _make_settings(data_dir=str(tmp_path))
        client = AgentClient(settings)

        # Cache also has empty digest — must NOT skip
        save(tmp_path, "nginx:latest", {"ArtifactName": "nginx:latest"}, image_digest="")

        mock_ws = AsyncMock()
        scan_result = {"ArtifactName": "nginx:latest", "Results": []}
        containers = [{"image_name": "nginx:latest", "container_name": "my-nginx", "image_digest": ""}]

        with (
            patch("trivyal_agent.ws.client.list_running_images", return_value=containers),
            patch("trivyal_agent.ws.client.scan_all_images", return_value=[scan_result]) as mock_scan,
            patch("trivyal_agent.ws.client.save"),
            patch("trivyal_agent.ws.client.run_misconfig_checks", return_value=[]),
        ):
            await client._run_scan_cycle(mock_ws)

        mock_scan.assert_called_once_with(["nginx:latest"])

    async def test_misconfig_checks_run_even_when_all_images_skipped(self, tmp_path):
        from trivyal_agent.core.cache import save

        settings = _make_settings(data_dir=str(tmp_path))
        client = AgentClient(settings)

        save(tmp_path, "nginx:latest", {"ArtifactName": "nginx:latest"}, image_digest="sha256:abc")

        mock_ws = AsyncMock()
        sent = []
        mock_ws.send = AsyncMock(side_effect=lambda m: sent.append(json.loads(m)))

        containers = [{"image_name": "nginx:latest", "container_name": "my-nginx", "image_digest": "sha256:abc"}]
        misconfig_result = {
            "container_id": "abc",
            "container_name": "my-nginx",
            "image_name": "nginx:latest",
            "findings": [
                {"check_id": "NET_001", "severity": "MEDIUM", "title": "Host network", "fix_guideline": "Fix it"}
            ],
        }

        with (
            patch("trivyal_agent.ws.client.list_running_images", return_value=containers),
            patch("trivyal_agent.ws.client.scan_all_images", return_value=[]),
            patch("trivyal_agent.ws.client.run_misconfig_checks", return_value=[misconfig_result]),
        ):
            await client._run_scan_cycle(mock_ws)

        assert any(m["type"] == "misconfig_result" for m in sent)

    async def test_digest_persisted_to_cache_after_scan(self, tmp_path):
        from trivyal_agent.core.cache import get_cached_digest

        settings = _make_settings(data_dir=str(tmp_path))
        client = AgentClient(settings)

        mock_ws = AsyncMock()
        scan_result = {"ArtifactName": "alpine:3", "Results": []}
        containers = [{"image_name": "alpine:3", "container_name": "c1", "image_digest": "sha256:xyz"}]

        with (
            patch("trivyal_agent.ws.client.list_running_images", return_value=containers),
            patch("trivyal_agent.ws.client.scan_all_images", return_value=[scan_result]),
            patch("trivyal_agent.ws.client.run_misconfig_checks", return_value=[]),
        ):
            await client._run_scan_cycle(mock_ws)

        assert get_cached_digest(tmp_path, "alpine:3") == "sha256:xyz"


class TestFlushCache:
    """Tests for _flush_cache — specifically the cache-clearing postcondition.

    Before the fix, _flush_cache sent cached results but never deleted the files.
    Every reconnect would re-send the same N results indefinitely.
    """

    def _result(self, image: str) -> dict:
        return {"ArtifactName": image, "Results": []}

    async def test_deletes_cache_file_after_successful_send(self, tmp_path):
        from trivyal_agent.core.cache import list_cached, save

        settings = _make_settings(data_dir=str(tmp_path))
        client = AgentClient(settings)
        save(tmp_path, "nginx:latest", self._result("nginx:latest"))

        mock_ws = AsyncMock()
        await client._flush_cache(mock_ws)

        assert list_cached(tmp_path) == []

    async def test_deletes_all_files_when_all_sends_succeed(self, tmp_path):
        from trivyal_agent.core.cache import list_cached, save

        settings = _make_settings(data_dir=str(tmp_path))
        client = AgentClient(settings)
        save(tmp_path, "nginx:latest", self._result("nginx:latest"))
        save(tmp_path, "redis:7", self._result("redis:7"))

        mock_ws = AsyncMock()
        await client._flush_cache(mock_ws)

        assert list_cached(tmp_path) == []

    async def test_keeps_file_when_send_fails(self, tmp_path):
        """A failed send must leave the cache file intact so the result is
        retried on the next reconnect."""
        from trivyal_agent.core.cache import list_cached, save

        settings = _make_settings(data_dir=str(tmp_path))
        client = AgentClient(settings)
        save(tmp_path, "nginx:latest", self._result("nginx:latest"))

        mock_ws = AsyncMock()
        mock_ws.send = AsyncMock(side_effect=Exception("connection lost"))

        await client._flush_cache(mock_ws)  # must not raise

        remaining = list_cached(tmp_path)
        assert len(remaining) == 1
        assert remaining[0][0]["ArtifactName"] == "nginx:latest"

    async def test_partial_flush_clears_only_sent_files(self, tmp_path):
        """If the second send fails, only the first file should be deleted."""
        from trivyal_agent.core.cache import list_cached, save

        settings = _make_settings(data_dir=str(tmp_path))
        client = AgentClient(settings)
        save(tmp_path, "nginx:latest", self._result("nginx:latest"))
        save(tmp_path, "redis:7", self._result("redis:7"))

        send_calls = []

        async def _send_side_effect(data):
            send_calls.append(json.loads(data)["data"]["ArtifactName"])
            if len(send_calls) == 2:
                raise Exception("dropped")

        mock_ws = AsyncMock()
        mock_ws.send = AsyncMock(side_effect=_send_side_effect)

        await client._flush_cache(mock_ws)

        remaining = list_cached(tmp_path)
        assert len(remaining) == 1  # one deleted, one kept for retry

    async def test_flush_preserves_container_name(self, tmp_path):
        """container_name saved alongside the result must be sent during flush."""
        from trivyal_agent.core.cache import save

        settings = _make_settings(data_dir=str(tmp_path))
        client = AgentClient(settings)
        save(tmp_path, "nginx:latest", self._result("nginx:latest"), container_name="my-nginx")

        sent = []
        mock_ws = AsyncMock()
        mock_ws.send = AsyncMock(side_effect=lambda m: sent.append(json.loads(m)))

        await client._flush_cache(mock_ws)

        assert len(sent) == 1
        assert sent[0]["type"] == "scan_result"
        assert sent[0]["container_name"] == "my-nginx"

    async def test_noop_when_cache_is_empty(self, tmp_path):
        settings = _make_settings(data_dir=str(tmp_path))
        client = AgentClient(settings)

        mock_ws = AsyncMock()
        await client._flush_cache(mock_ws)

        mock_ws.send.assert_not_called()
