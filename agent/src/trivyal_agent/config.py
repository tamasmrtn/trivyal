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
    reconnect_delay: int = 10  # base seconds before reconnect attempt
    max_reconnect_delay: int = 300  # cap for exponential backoff
    reconnect_jitter: float = 0.25  # ±25% random jitter on reconnect delay
    connect_timeout: int = 15  # seconds for initial WebSocket connection
    initial_connect_jitter: int = 30  # max seconds to stagger first connection
    health_port: int = 8100  # port for the HTTP health endpoint
    max_scan_age_days: int = 3  # force rescan after this many days even if digest unchanged


settings = Settings()
