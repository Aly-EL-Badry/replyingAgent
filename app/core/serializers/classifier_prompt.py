"""
app/core/serializers/classifier_prompt.py
------------------------------------------
Pydantic serializer for the comment classifier configuration block.

Maps to the 'classifier' and 'private_reply' sections in config/classifierPrompt.yaml.
"""
from pydantic import BaseModel


class ClassifierPromptConfig(BaseModel):
    system_prompt: str


class PrivateReplyPromptConfig(BaseModel):
    system_prompt: str


class ClassifierPrompt(BaseModel):
    """Top-level container loaded from classifierPrompt.yaml."""
    classifier: ClassifierPromptConfig
    private_reply: PrivateReplyPromptConfig
