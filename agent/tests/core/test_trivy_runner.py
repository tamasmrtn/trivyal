"""Tests for core/trivy_runner.py."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from trivyal_agent.core.trivy_runner import TrivyError, scan_all_images, scan_image

SAMPLE_TRIVY_OUTPUT = {
    "ArtifactName": "nginx:latest",
    "ArtifactType": "container_image",
    "Results": [
        {
            "Target": "nginx:latest (debian 12.4)",
            "Vulnerabilities": [
                {
                    "VulnerabilityID": "CVE-2024-0001",
                    "PkgName": "openssl",
                    "InstalledVersion": "3.0.1",
                    "FixedVersion": "3.0.2",
                    "Severity": "HIGH",
                }
            ],
        }
    ],
}


class TestScanImage:
    async def test_returns_parsed_json_on_success(self):
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.communicate = AsyncMock(return_value=(json.dumps(SAMPLE_TRIVY_OUTPUT).encode(), b""))

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            result = await scan_image("nginx:latest")

        assert result["ArtifactName"] == "nginx:latest"
        assert len(result["Results"]) == 1

    async def test_raises_on_nonzero_exit(self):
        mock_proc = MagicMock()
        mock_proc.returncode = 1
        mock_proc.communicate = AsyncMock(return_value=(b"", b"some error"))

        with (
            patch("asyncio.create_subprocess_exec", return_value=mock_proc),
            pytest.raises(TrivyError, match="exited with code 1"),
        ):
            await scan_image("nginx:latest")

    async def test_raises_when_trivy_not_found(self):
        with (
            patch("asyncio.create_subprocess_exec", side_effect=FileNotFoundError),
            pytest.raises(TrivyError, match="trivy binary not found"),
        ):
            await scan_image("nginx:latest")

    async def test_raises_on_empty_output(self):
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.communicate = AsyncMock(return_value=(b"", b""))

        with (
            patch("asyncio.create_subprocess_exec", return_value=mock_proc),
            pytest.raises(TrivyError, match="no output"),
        ):
            await scan_image("nginx:latest")

    async def test_raises_on_invalid_json(self):
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.communicate = AsyncMock(return_value=(b"not json", b""))

        with (
            patch("asyncio.create_subprocess_exec", return_value=mock_proc),
            pytest.raises(TrivyError, match="not valid JSON"),
        ):
            await scan_image("nginx:latest")


class TestScanAllImages:
    async def test_returns_results_for_successful_scans(self):
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.communicate = AsyncMock(return_value=(json.dumps(SAMPLE_TRIVY_OUTPUT).encode(), b""))

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            results = await scan_all_images(["nginx:latest"])

        assert len(results) == 1
        assert results[0]["ArtifactName"] == "nginx:latest"

    async def test_skips_failed_images(self):
        mock_proc = MagicMock()
        mock_proc.returncode = 1
        mock_proc.communicate = AsyncMock(return_value=(b"", b"error"))

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            results = await scan_all_images(["bad-image:latest"])

        assert results == []

    async def test_returns_empty_list_for_no_images(self):
        results = await scan_all_images([])
        assert results == []
