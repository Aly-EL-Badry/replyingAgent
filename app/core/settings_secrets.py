from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]
DOTENV_PATH = BASE_DIR / ".env"

class SecretSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=DOTENV_PATH,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    hf_token: str = Field(default=..., validation_alias="HF_TOKEN")
    fb_token: str = Field(default=..., validation_alias="FB_TOKEN")
    fb_verify_token: str = Field(default=..., validation_alias="FB_VERIFY_TOKEN")

secrets = SecretSettings()