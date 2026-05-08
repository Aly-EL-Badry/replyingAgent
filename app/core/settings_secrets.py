from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv
import os

BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DOTENV_PATH: str = os.path.join(BASE_DIR, ".env")

if os.path.exists(DOTENV_PATH):
    load_dotenv(DOTENV_PATH)

class SecretSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=DOTENV_PATH,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    hf_token: str = Field(default=..., validation_alias="HF_TOKEN")
    fb_token: str = Field(default=..., validation_alias="FB_TOKEN")
    fb_verify_token: str = Field(default=..., validation_alias="FB_VERIFY_TOKEN")

    # Weaviate — optional (defaults allow local / embedded mode)
    weaviate_url: str = Field(default="http://localhost:8080", validation_alias="WEAVIATE_URL")
    weaviate_api_key: str | None = Field(default=None, validation_alias="WEAVIATE_API_KEY")

secrets = SecretSettings()