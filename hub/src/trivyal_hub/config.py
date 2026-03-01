"""Application settings loaded from environment variables."""

from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_prefix": "TRIVYAL_"}

    secret_key: str = "change-me"
    data_dir: Path = Path("/app/data")
    host: str = "0.0.0.0"
    port: int = 8099
    admin_password: str = "admin"
    database_url: str | None = None

    @property
    def db_url(self) -> str:
        if self.database_url:
            return self.database_url
        db_path = self.data_dir / "trivyal.db"
        return f"sqlite+aiosqlite:///{db_path}"


settings = Settings()
