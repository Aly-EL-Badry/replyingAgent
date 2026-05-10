from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ConversationMessage:
    """A single turn in a conversation."""
    role:    str   # "user" | "assistant" | "system"
    content: str
