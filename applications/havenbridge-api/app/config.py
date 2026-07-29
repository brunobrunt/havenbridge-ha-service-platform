"""
Central configuration for the HavenBridge API.

This module improves the application by keeping configuration separate from
the business logic. It reads settings from environment variables during local
development and from Kubernetes ConfigMaps and Secrets in the cluster.

Sensitive values, such as the PostgreSQL password, are never hard-coded here.
"""

from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Validate and expose configuration required by the HavenBridge API.

    Environment-variable examples:

        APP_ENVIRONMENT=production
        POSTGRES_HOST=havenbridge-postgres
        POSTGRES_PORT=5432
        POSTGRES_DB=havenbridge
        POSTGRES_USER=havenbridge_admin
        POSTGRES_PASSWORD_FILE=/run/secrets/postgres-password
    """

    # General API configuration.
    app_name: str = "HavenBridge API"
    app_environment: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = Field(default=8000, ge=1, le=65535)
    log_level: str = "INFO"

    # PostgreSQL connection details.
    # Kubernetes will override the local host value using a ConfigMap.
    postgres_host: str = "127.0.0.1"
    postgres_port: int = Field(default=5432, ge=1, le=65535)
    postgres_db: str = "havenbridge"
    postgres_user: str = "havenbridge_admin"

    # Local development may provide POSTGRES_PASSWORD directly.
    # SecretStr prevents the password from being printed accidentally.
    postgres_password: SecretStr | None = None

    # Kubernetes will mount the PostgreSQL password as a file.
    # Reading a mounted Secret avoids placing the password in a manifest.
    postgres_password_file: Path | None = None

    # Database connection-pool configuration.
    # Pooling allows the API to reuse connections rather than opening a new
    # PostgreSQL connection for every incoming request.
    db_pool_size: int = Field(default=5, ge=1)
    db_max_overflow: int = Field(default=10, ge=0)
    db_connect_timeout_seconds: int = Field(default=5, ge=1)
    # Create missing database tables when the API starts in development.
    #
    # This is useful while we are building the first version of HavenBridge.
    # Alembic migrations will replace this before production-style deployment.
    db_auto_create_tables: bool = True
    model_config = SettingsConfigDict(
        # The .env file is intended only for local development.
        env_file=".env",
        env_file_encoding="utf-8",

        # POSTGRES_HOST and postgres_host are treated as the same setting.
        case_sensitive=False,

        # Ignore unrelated variables provided by the operating environment.
        extra="ignore",
    )

    def get_postgres_password(self) -> str:
        """
        Return the PostgreSQL password without exposing it in logs.

        Kubernetes-mounted Secret files take priority over a direct environment
        variable. This allows the same application code to run locally and in
        Kubernetes without hard-coding credentials.
        """

        if self.postgres_password_file is not None:
            try:
                password = self.postgres_password_file.read_text(
                    encoding="utf-8"
                ).strip()
            except OSError as exc:
                raise ValueError(
                    "Unable to read POSTGRES_PASSWORD_FILE."
                ) from exc

            if not password:
                raise ValueError(
                    "POSTGRES_PASSWORD_FILE exists but is empty."
                )

            return password

        if self.postgres_password is not None:
            return self.postgres_password.get_secret_value()

        raise ValueError(
            "Set POSTGRES_PASSWORD or POSTGRES_PASSWORD_FILE."
        )


@lru_cache
def get_settings() -> Settings:
    """
    Load and cache application settings.

    Caching prevents the application from rereading environment variables and
    Secret files for every API request.
    """

    return Settings()
