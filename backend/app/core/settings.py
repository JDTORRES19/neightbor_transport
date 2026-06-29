from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Transporte Vecinal API"
    app_version: str = "0.1.0"
    enable_docs: bool = True
    db_name: str = "test_db"
    db_user: str = "test_user"
    db_password: str = "postgres"
    db_host: str = "db"
    db_port: int = 5432
    cors_origins_raw: str = "http://localhost:5173,http://127.0.0.1:5173"
    enable_scheduler: bool = True
    scheduler_interval_seconds: int = 60

    def database_url(self) -> str:
        return (
            f"postgresql+psycopg2://{self.db_user}:{self.db_password}@"
            f"{self.db_host}:{self.db_port}/{self.db_name}"
        )

    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins_raw.split(",") if origin.strip()]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
