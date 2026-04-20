"""
Pydantic serializer models for application configuration.
"""
from pydantic import BaseModel

class Prompt(BaseModel):
    system_prompt: str
