from __future__ import annotations

from typing import Any

import httpx
from facebook import GraphAPI
from app.core.settings_secrets import secrets
from app.core.settings_constant import constants


class FacebookClient:
    """Wrapper around facebook-sdk's GraphAPI and direct HTTP for Facebook APIs."""

    def __init__(self, access_token: str | None = None) -> None:
        self._token = access_token or secrets.fb_token
        # The facebook-sdk only knows versions up to 3.1; we pass version=None
        # so it uses its own bundled default.  Our httpx-based calls (Messenger)
        # always use the full versioned URL from config instead.
        self._graph = GraphAPI(access_token=self._token)
        self._base_url = constants.facebook.graph_api_base_url
        self._timeout = constants.facebook.request_timeout

    def post_reply(self, comment_id: str, reply_text: str) -> Any:
        """Post a reply to a Facebook comment."""
        response = self._graph.put_comment(object_id=comment_id, message=reply_text)
        return response

    async def send_messenger_message(self, recipient_id: str, text: str) -> Any:
        url = f"{self._base_url}/{constants.facebook.graph_api_version}/me/messages"
        payload = {
            "recipient": {"id": recipient_id},
            "message": {"text": text},
        }
        params = {"access_token": self._token}

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(url, json=payload, params=params)
            response.raise_for_status()
            return response.json()


facebook_client = FacebookClient()
