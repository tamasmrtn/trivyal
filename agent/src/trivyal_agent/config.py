"""Agent settings loaded from environment variables."""

from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_prefix": "TRIVYAL_"}

    hub_url: str = "ws://localhost:8099"
    token: str = ""
    key: str = ""  # Hub Ed25519 public key (base64-encoded)
    scan_schedule: str = "0 2 * * *"  # cron expression, default 2am nightly
    data_dir: Path = Path("/app/data")
    agent_version: str = "0.1.0"
    heartbeat_interval: int = 30  # seconds between heartbeats
    reconnect_delay: int = 10  # seconds before reconnect attempt


settings = Settings()
