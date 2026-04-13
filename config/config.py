"""
config/config.py
----------------
Single Settings class built on pydantic-settings.

- Non-secret values come from config/config.yaml (via YamlConfigSource)
- Secrets (tokens) come from environment / .env
- Import the ready-made singleton:  from config.config import settings
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Tuple, Type

import yaml
from pydantic import Field
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)
from config.serializers import FacebookSettings, HuggingFaceSettings, ReplySettings

_CONFIG_PATH = Path(__file__).parent / "config.yaml"



class YamlConfigSource(PydanticBaseSettingsSource):
    """Feeds config.yaml into pydantic-settings as a settings source."""

    def get_field_value(self, field: Any, field_name: str) -> Any:  
        return None, field_name, False

    def __call__(self) -> dict[str, Any]:
        with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}



class Settings(BaseSettings):
    """
    Central application settings.

    Usage
    -----
        from config.config import settings

        settings.huggingface.model_id
        settings.hf_token          # secret, from env / .env
        settings.fb_token          # secret, from env / .env
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    huggingface: HuggingFaceSettings
    facebook: FacebookSettings
    reply: ReplySettings

    hf_token: str = Field(validation_alias="HF_TOKEN")
    fb_token: str = Field(validation_alias="FB_TOKEN")

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        secrets_dir_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            YamlConfigSource(settings_cls),
        )


settings = Settings()
