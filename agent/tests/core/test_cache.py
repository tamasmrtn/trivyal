"""Tests for core/cache.py — digest storage and retrieval."""

import json
import stat
import time

from trivyal_agent.core.cache import get_cached_digest, is_cache_stale, list_cached, load, save


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

    def test_persists_scanned_at_timestamp(self, tmp_path):
        ts = 1_000_000.0
        save(tmp_path, "alpine:3", {}, scanned_at=ts)
        raw = json.loads((tmp_path / "cache" / "alpine_3.json").read_text())
        assert raw["scanned_at"] == ts

    def test_scanned_at_defaults_to_current_time(self, tmp_path):
        before = time.time()
        save(tmp_path, "alpine:3", {})
        after = time.time()
        raw = json.loads((tmp_path / "cache" / "alpine_3.json").read_text())
        assert before <= raw["scanned_at"] <= after


class TestIsCacheStale:
    def test_returns_true_when_no_cache_file(self, tmp_path):
        assert is_cache_stale(tmp_path, "nginx:latest", max_age_days=7) is True

    def test_returns_false_when_cache_is_fresh(self, tmp_path):
        save(tmp_path, "nginx:latest", {}, scanned_at=time.time())
        assert is_cache_stale(tmp_path, "nginx:latest", max_age_days=7) is False

    def test_returns_true_when_cache_exceeds_max_age(self, tmp_path):
        eight_days_ago = time.time() - 8 * 86400
        save(tmp_path, "nginx:latest", {}, scanned_at=eight_days_ago)
        assert is_cache_stale(tmp_path, "nginx:latest", max_age_days=7) is True

    def test_returns_true_for_old_format_cache_without_scanned_at(self, tmp_path):
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        (cache_dir / "nginx_latest.json").write_text(
            json.dumps({"result": {}, "container_name": None, "image_digest": "sha256:abc"})
        )
        assert is_cache_stale(tmp_path, "nginx:latest", max_age_days=7) is True

    def test_returns_true_for_corrupt_cache(self, tmp_path):
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        (cache_dir / "nginx_latest.json").write_text("not json{{{")
        assert is_cache_stale(tmp_path, "nginx:latest", max_age_days=7) is True

    def test_exactly_at_max_age_boundary_is_stale(self, tmp_path):
        exactly_seven_days_ago = time.time() - 7 * 86400
        save(tmp_path, "nginx:latest", {}, scanned_at=exactly_seven_days_ago)
        assert is_cache_stale(tmp_path, "nginx:latest", max_age_days=7) is True


class TestLoad:
    def test_returns_result_and_container_name(self, tmp_path):
        result = {"ArtifactName": "nginx:latest", "Results": []}
        save(tmp_path, "nginx:latest", result, container_name="my-nginx")
        loaded = load(tmp_path, "nginx:latest")
        assert loaded is not None
        assert loaded[0] == result
        assert loaded[1] == "my-nginx"

    def test_returns_none_when_no_cache(self, tmp_path):
        assert load(tmp_path, "nonexistent:image") is None

    def test_returns_none_on_corrupt_file(self, tmp_path):
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        (cache_dir / "nginx_latest.json").write_text("not valid json{{{")
        assert load(tmp_path, "nginx:latest") is None


class TestSaveErrorHandling:
    def test_handles_write_error_gracefully(self, tmp_path):
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        # Make cache dir read-only so write fails
        cache_dir.chmod(stat.S_IRUSR | stat.S_IXUSR)
        try:
            # Should not raise despite write failure
            save(tmp_path, "nginx:latest", {"ArtifactName": "nginx:latest"})
        finally:
            # Restore permissions for cleanup
            cache_dir.chmod(stat.S_IRWXU)


class TestListCachedErrorHandling:
    def test_skips_corrupt_files(self, tmp_path):
        # Save one valid entry
        save(tmp_path, "nginx:latest", {"ArtifactName": "nginx:latest"}, container_name="c1")
        # Write one corrupt file
        (tmp_path / "cache" / "corrupt_image.json").write_text("not json{{{")

        results = list_cached(tmp_path)
        assert len(results) == 1
        assert results[0][0]["ArtifactName"] == "nginx:latest"
