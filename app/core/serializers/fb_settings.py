from pydantic import BaseModel

class FacebookSettings(BaseModel):
    graph_api_version: str
    graph_api_base_url: str
    request_timeout: int = 10
