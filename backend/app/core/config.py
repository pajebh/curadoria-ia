from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Banco
    database_url: str

    # Redis
    redis_url: str

    # JWT
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_ttl_days: int = 180

    # IA
    groq_api_key: str = ""
    gemini_api_key: str = ""
    google_cse_key: str = ""
    google_cse_id: str = ""

    # App
    environment: str = "development"
    log_level: str = "INFO"

    # Observabilidade
    sentry_dsn: str = ""
    logtail_token: str = ""

    # CORS — str simples para evitar JSON-parse do pydantic-settings v2
    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


settings = Settings()  # type: ignore[call-arg]
