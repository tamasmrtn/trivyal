"""Agent settings loaded from environment variables."""

import importlib.metadata
from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_prefix": "TRIVYAL_"}

    hub_url: str = "ws://localhost:8099"
    token: SecretStr = SecretStr("")
    key: SecretStr = SecretStr("")  # Hub Ed25519 public key (base64-encoded)
    scan_schedule: str = "0 2 * * *"  # cron expression, default 2am nightly
    data_dir: Path = Path("/app/data")
    agent_version: str = Field(default_factory=lambda: importlib.metadata.version("trivyal-agent"))
    heartbeat_interval: int = 30  # seconds between heartbeats
    reconnect_delay: int = 10  # seconds before reconnect attempt
    max_scan_age_days: int = 3  # force rescan after this many days even if digest unchanged


settings = Settings()
