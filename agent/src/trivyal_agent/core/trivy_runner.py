"""Invoke Trivy CLI and parse JSON output."""

import asyncio
import json
import logging

logger = logging.getLogger(__name__)


class TrivyError(Exception):
    """Raised when Trivy exits with a non-zero status or produces invalid output."""


async def scan_image(image_name: str) -> dict:
    """Run `trivy image --format json` against *image_name* and return parsed JSON.

    Raises:
        TrivyError: if Trivy is not found, exits non-zero, or produces invalid JSON.
    """
    logger.info("Scanning image: %s", image_name)

    try:
        proc = await asyncio.create_subprocess_exec(
            "trivy",
            "image",
            "--format",
            "json",
            "--quiet",
            image_name,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
    except FileNotFoundError as exc:
        raise TrivyError("trivy binary not found — is it installed?") from exc

    stdout, stderr = await proc.communicate()

    if proc.returncode != 0:
        raise TrivyError(f"trivy exited with code {proc.returncode}: {stderr.decode(errors='replace')}")

    raw = stdout.decode(errors="replace").strip()
    if not raw:
        raise TrivyError(f"trivy produced no output for image {image_name}")

    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise TrivyError(f"trivy output is not valid JSON: {exc}") from exc


async def scan_all_images(image_names: list[str]) -> list[dict]:
    """Scan each image sequentially and return a list of Trivy results.

    Images that fail to scan are logged and skipped.
    """
    results = []
    for image_name in image_names:
        try:
            result = await scan_image(image_name)
            results.append(result)
        except TrivyError:
            logger.exception("Failed to scan image %s — skipping", image_name)
    return results
