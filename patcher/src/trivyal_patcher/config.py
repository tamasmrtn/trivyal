"""Patcher sidecar settings loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_prefix": "TRIVYAL_PATCHER_"}

    port: int = 8101
    docker_socket: str = "/var/run/docker.sock"
    copa_binary: str = "copa"
    copa_timeout: str = "30m"
    buildkitd_addr: str = "tcp://127.0.0.1:1234"


settings = Settings()
