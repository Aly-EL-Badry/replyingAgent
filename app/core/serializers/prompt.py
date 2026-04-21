"""
Pydantic serializer models for application configuration.
"""
from typing import Any
from pydantic import BaseModel, model_validator


class Prompt(BaseModel):
    system_prompt: str

    @model_validator(mode="before")
    @classmethod
    def coerce_string(cls, v: Any) -> Any:
        """Allow the YAML scalar shorthand (reply: >) to be used directly."""
        if isinstance(v, str):
            return {"system_prompt": v}
        return v
