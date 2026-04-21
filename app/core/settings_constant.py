from click import prompt
import yaml
from pathlib import Path
from typing import Any, Tuple, Type

from pydantic import Field
from pydantic_settings import (
    BaseSettings, 
    PydanticBaseSettingsSource, 
    SettingsConfigDict
)
from .serializers.fb_settings import FacebookSettings
from .serializers.hf_settings import HuggingFaceSettings
from .serializers.prompt import Prompt

CONFIG_DIR = Path(__file__).resolve().parents[2] / "config"

class ConfigSource(PydanticBaseSettingsSource):
    """Dynamically loads all YAML files from the config folder."""
    
    def __call__(self) -> dict[str, Any]:
        config_data = {}
        if not CONFIG_DIR.exists():
            return config_data

        for file_path in CONFIG_DIR.glob("*.y*ml"):
            with open(file_path, "r", encoding="utf-8") as f:
                content = yaml.safe_load(f)
                if isinstance(content, dict):
                    config_data.update(content)
        return config_data

class ConstantSettings(BaseSettings):

    model_config = SettingsConfigDict(env_file=None)

    facebook: FacebookSettings = Field(default=...)
    huggingface: HuggingFaceSettings = Field(default=...)
    reply: Prompt = Field(default=...)

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        return (init_settings, ConfigSource(settings_cls))


constants = ConstantSettings()