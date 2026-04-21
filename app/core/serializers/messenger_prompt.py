"""
Pydantic serializer for Messenger-specific configuration.
"""
from pydantic import BaseModel


class MessengerPrompt(BaseModel):
    system_prompt: str
