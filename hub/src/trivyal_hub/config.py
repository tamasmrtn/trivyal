"""Application settings loaded from environment variables."""

from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_prefix": "TRIVYAL_"}

    secret_key: SecretStr = SecretStr("change-me")
    data_dir: Path = Path("/app/data")
    host: str = "0.0.0.0"  # noqa: S104  # nosec B104 — bind all interfaces for Docker
    port: int = 8099
    admin_password: SecretStr = SecretStr("admin")
    database_url: str | None = None
    static_dir: Path = Path("/app/static")

    @property
    def db_url(self) -> str:
        if self.database_url:
            return self.database_url
        db_path = self.data_dir / "trivyal.db"
        return f"sqlite+aiosqlite:///{db_path}"


settings = Settings()
