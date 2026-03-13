"""Tests for core/cache.py — digest storage and retrieval."""

import json

from trivyal_agent.core.cache import get_cached_digest, save


class TestGetCachedDigest:
    def test_returns_empty_string_when_no_cache_file(self, tmp_path):
        assert get_cached_digest(tmp_path, "nginx:latest") == ""

    def test_returns_stored_digest(self, tmp_path):
        save(tmp_path, "nginx:latest", {"ArtifactName": "nginx:latest"}, image_digest="sha256:abc123")
        assert get_cached_digest(tmp_path, "nginx:latest") == "sha256:abc123"

    def test_returns_empty_string_for_old_format_cache_without_digest_key(self, tmp_path):
        # Simulate a cache file written before the image_digest field was added
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        (cache_dir / "nginx_latest.json").write_text(
            json.dumps({"result": {"ArtifactName": "nginx:latest"}, "container_name": "my-nginx"})
        )
        assert get_cached_digest(tmp_path, "nginx:latest") == ""

    def test_returns_empty_string_for_corrupt_cache_file(self, tmp_path):
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        (cache_dir / "nginx_latest.json").write_text("not valid json{{{")
        assert get_cached_digest(tmp_path, "nginx:latest") == ""

    def test_different_images_have_independent_digests(self, tmp_path):
        save(tmp_path, "nginx:latest", {}, image_digest="sha256:aaa")
        save(tmp_path, "redis:7", {}, image_digest="sha256:bbb")
        assert get_cached_digest(tmp_path, "nginx:latest") == "sha256:aaa"
        assert get_cached_digest(tmp_path, "redis:7") == "sha256:bbb"


class TestSaveWithDigest:
    def test_persists_image_digest(self, tmp_path):
        save(tmp_path, "alpine:3", {"ArtifactName": "alpine:3"}, image_digest="sha256:xyz")
        raw = json.loads((tmp_path / "cache" / "alpine_3.json").read_text())
        assert raw["image_digest"] == "sha256:xyz"

    def test_default_digest_is_empty_string(self, tmp_path):
        save(tmp_path, "alpine:3", {"ArtifactName": "alpine:3"})
        raw = json.loads((tmp_path / "cache" / "alpine_3.json").read_text())
        assert raw["image_digest"] == ""

    def test_existing_result_and_container_name_still_persisted(self, tmp_path):
        result = {"ArtifactName": "alpine:3", "Results": []}
        save(tmp_path, "alpine:3", result, container_name="my-alpine", image_digest="sha256:abc")
        raw = json.loads((tmp_path / "cache" / "alpine_3.json").read_text())
        assert raw["result"] == result
        assert raw["container_name"] == "my-alpine"
        assert raw["image_digest"] == "sha256:abc"
