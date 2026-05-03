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


def _load_yaml_config() -> dict[str, Any]:
    """Load and merge all YAML files from the config directory."""
    config_data: dict[str, Any] = {}
    if not CONFIG_DIR.exists():
        return config_data
    for file_path in CONFIG_DIR.glob("*.y*ml"):
        with open(file_path, "r", encoding="utf-8") as f:
            content = yaml.safe_load(f)
            if isinstance(content, dict):
                config_data.update(content)
    return config_data


class ConfigSource(PydanticBaseSettingsSource):
    """Dynamically loads all YAML files from the config folder."""

    def __init__(self, settings_cls: Type[BaseSettings]) -> None:
        super().__init__(settings_cls)
        self._data = _load_yaml_config()

    def get_field_value(self, field: Any, field_name: str) -> Any:  
        return self._data.get(field_name), field_name, False

    def __call__(self) -> dict[str, Any]:
        return {
            field_name: self.get_field_value(field_info, field_name)[0]
            for field_name, field_info in self.settings_cls.model_fields.items()
            if self.get_field_value(field_info, field_name)[0] is not None
        }

class ConstantSettings(BaseSettings):

    model_config = SettingsConfigDict(env_file=None)

    facebook: FacebookSettings = Field(default=...)
    huggingface: HuggingFaceSettings = Field(default=...)
    reply: Prompt = Field(default=...)
    messenger: Prompt = Field(default=...)
    classifier: Prompt = Field(default=...)
    private_reply: Prompt = Field(default=...)

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