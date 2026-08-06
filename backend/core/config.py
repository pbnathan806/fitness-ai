from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "postgres"
    postgres_password: str = "postgres"
    postgres_db: str = "fitness_ai"

    database_pool_min_size: int = 1
    database_pool_max_size: int = 10

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30

    password_reset_token_expire_minutes: int = 30

    # Only read in production (see routers/auth.py::get_password_reset_notifier);
    # local/dev environments use ConsolePasswordResetNotifier instead, so
    # these are safe to leave unset for local development.
    resend_api_key: str = ""
    resend_from_email: str = "Fitness AI Platform <noreply@limitedeals.com>"
    # Used to build the clickable reset-password link embedded in the email
    # (the backend has no other way to know the frontend's public URL).
    frontend_base_url: str = "http://localhost:5173"

    postgres_ssl_mode: str = "disable"
    cors_allowed_origins: str = "http://localhost:5173"

    # "production" disables the public /docs, /redoc, and /openapi.json
    # routes (see main.py) so the API schema isn't handed out to anyone who
    # asks; every other environment keeps them on for local/manual testing.
    environment: str = "development"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def is_production(self) -> bool:
        return self.environment.strip().lower() == "production"

    @property
    def database_dsn(self) -> str:
        dsn = (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )
        if self.postgres_ssl_mode == "require":
            dsn += "?ssl=require"
        return dsn

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]


settings = Settings()
