"""Copa subprocess wrapper — patches container images using Copa."""

import asyncio
import json
import logging
import tempfile
from collections.abc import AsyncGenerator
from pathlib import Path

from trivyal_patcher.config import settings

logger = logging.getLogger(__name__)


async def run_copa(
    image: str,
    trivy_report: dict,
    patched_tag: str,
) -> AsyncGenerator[dict]:
    """Run Copa to patch an image. Yields NDJSON log lines and a final result."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(trivy_report, f)
        report_path = f.name

    try:
        cmd = [
            settings.copa_binary,
            "patch",
            "-i", image,
            "-r", report_path,
            "-t", patched_tag,
            "--addr", settings.buildkitd_addr,
            "--timeout", settings.copa_timeout,
            "--progress", "plain",
        ]

        logger.info("Running Copa: %s", " ".join(cmd))
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )

        assert proc.stdout is not None
        async for line in proc.stdout:
            text = line.decode(errors="replace").rstrip()
            if text:
                yield {"type": "log", "line": text}

        returncode = await proc.wait()

        if returncode == 0:
            yield {"type": "result", "status": "completed", "patched_tag": patched_tag}
        else:
            yield {"type": "result", "status": "failed", "error": f"Copa exited with code {returncode}"}
    finally:
        Path(report_path).unlink(missing_ok=True)
