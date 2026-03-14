"""Local result cache — persists last Trivy scan results to disk as JSON.

Used for resilience when the hub is temporarily unreachable: the agent stores
each scan result locally and can re-send them after reconnection.
"""

import contextlib
import json
import logging
import re
import time
from pathlib import Path

logger = logging.getLogger(__name__)

_SAFE_NAME_RE = re.compile(r"[^\w.-]")


def _safe_filename(image_name: str) -> str:
    """Convert an image name to a safe filesystem filename."""
    return _SAFE_NAME_RE.sub("_", image_name)[:200] + ".json"


def save(
    data_dir: Path,
    image_name: str,
    result: dict,
    container_name: str | None = None,
    image_digest: str = "",
    scanned_at: float | None = None,
) -> None:
    """Persist a Trivy scan result for *image_name* to disk."""
    cache_dir = data_dir / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_dir / _safe_filename(image_name)
    try:
        cache_file.write_text(
            json.dumps(
                {
                    "result": result,
                    "container_name": container_name,
                    "image_digest": image_digest,
                    "scanned_at": scanned_at if scanned_at is not None else time.time(),
                }
            )
        )
    except OSError:
        logger.exception("Failed to write cache for %s", image_name)


def get_cached_digest(data_dir: Path, image_name: str) -> str:
    """Return the image digest stored in the cache for *image_name*, or '' if absent."""
    cache_file = data_dir / "cache" / _safe_filename(image_name)
    if not cache_file.exists():
        return ""
    try:
        entry = json.loads(cache_file.read_text())
        return entry.get("image_digest", "")
    except Exception:
        return ""


def is_cache_stale(data_dir: Path, image_name: str, max_age_days: int) -> bool:
    """Return True if the cached scan is older than *max_age_days* (or absent/corrupt)."""
    cache_file = data_dir / "cache" / _safe_filename(image_name)
    if not cache_file.exists():
        return True
    try:
        entry = json.loads(cache_file.read_text())
        scanned_at = entry.get("scanned_at")
        if scanned_at is None:
            return True  # old cache format — treat as stale
        return (time.time() - scanned_at) / 86400 >= max_age_days
    except Exception:
        return True


def load(data_dir: Path, image_name: str) -> tuple[dict, str | None] | None:
    """Load the cached Trivy scan result for *image_name*, or None if absent."""
    cache_file = data_dir / "cache" / _safe_filename(image_name)
    if not cache_file.exists():
        return None
    try:
        entry = json.loads(cache_file.read_text())
        return entry["result"], entry["container_name"]
    except Exception:
        logger.exception("Failed to read cache for %s", image_name)
        return None


def clear(data_dir: Path, image_name: str) -> None:
    """Delete the cached scan result for *image_name* from disk."""
    cache_file = data_dir / "cache" / _safe_filename(image_name)
    with contextlib.suppress(FileNotFoundError):
        cache_file.unlink()


def list_cached(data_dir: Path) -> list[tuple[dict, str | None]]:
    """Return all cached scan results from disk as (result, container_name) pairs."""
    cache_dir = data_dir / "cache"
    if not cache_dir.exists():
        return []
    results = []
    for cache_file in cache_dir.glob("*.json"):
        try:
            entry = json.loads(cache_file.read_text())
            results.append((entry["result"], entry["container_name"]))
        except Exception:
            logger.exception("Failed to read cache file %s", cache_file)
    return results
