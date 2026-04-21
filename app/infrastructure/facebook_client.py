from __future__ import annotations

from typing import Any

from facebook import GraphAPI
from app.core.settings_secrets import secrets
from app.core.settings_constant import constants

class FacebookClient:
    """Simple wrapper around facebook-sdk's GraphAPI for posting comment replies."""

    def __init__(self, access_token: str | None = None) -> None:
        self._token = access_token or secrets.fb_token
        self._graph = GraphAPI(access_token=self._token, version=constants.facebook.graph_api_version)

    def post_reply(self, comment_id: str, reply_text: str) -> Any:
        """Post a reply to a Facebook comment."""
        response = self._graph.put_comment(object_id=comment_id, message=reply_text)
        return response

facebook_client = FacebookClient()
