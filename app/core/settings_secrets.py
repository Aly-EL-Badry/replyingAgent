from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]  # Adjusted for project root
DOTENV_PATH = BASE_DIR / ".env"

# Load environment variables from .env if present (local development only)
if DOTENV_PATH.is_file():
    load_dotenv(DOTENV_PATH)

class SecretSettings(BaseSettings):
    # Load from .env if present, but do not require it.
    model_config = SettingsConfigDict(
        env_file=DOTENV_PATH,
        env_file_encoding="utf-8",
        env_file_required=False,
        extra="ignore",
    )

    hf_token: str = Field(default=..., validation_alias="HF_TOKEN")
    fb_token: str = Field(default=..., validation_alias="FB_TOKEN")
    fb_verify_token: str = Field(default=..., validation_alias="FB_VERIFY_TOKEN")

secrets = SecretSettings()