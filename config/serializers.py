"""
Pydantic serializer models for application configuration.
"""
from pydantic import BaseModel


class HuggingFaceSettings(BaseModel):
    model_id: str
    api_base_url: str
    max_new_tokens: int = 256
    temperature: float = 0.7
    top_p: float = 0.9
    repetition_penalty: float = 1.1
    request_timeout: int = 30


class FacebookSettings(BaseModel):
    graph_api_version: str
    graph_api_base_url: str
    request_timeout: int = 10


class ReplySettings(BaseModel):
    system_prompt: str
