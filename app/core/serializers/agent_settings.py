from pydantic import BaseModel


class AgentSettings(BaseModel):
    """Settings loaded from config/agentSettings.yaml."""
    base_url:                str  = "http://localhost:8000"
    ticket_prefix:           str  = "TK"
    order_prefix:            str  = "ORD"
    messenger_history_window: int = 10
