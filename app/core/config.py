from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "QuotePilot API"
    app_env: str = "dev"
    app_host: str = "127.0.0.1"
    app_port: int = 8000
    database_url: str = "sqlite:///./data/app.db"
    db_echo: bool = False
    openai_api_key: str = ""
    openai_base_url: str = ""
    local_model_name: str = "quote-risk-classifier"
    local_model_path: str = "models/quote_risk_model.joblib"
    local_text_model_name: str = "quote-text-classifier"
    local_text_model_path: str = "models/quote_text_classifier.joblib"
    upload_dir: str = "./uploads"
    allowed_file_types: list[str] = ["image/jpeg", "image/png", "image/gif", "image/bmp", "application/pdf"]
    allowed_extensions: list[str] = [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".pdf"]
    max_file_size_mb: int = 50

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
