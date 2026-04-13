"""
src/facebook/reply.py
---------------------
send_fb_reply(comment_id, reply_text) → None

Posts a reply to a Facebook comment via the Graph API.
"""
from __future__ import annotations

import httpx

from config.config import settings


async def send_fb_reply(comment_id: str, reply_text: str) -> None:
    """
    Post *reply_text* as a reply to *comment_id* on Facebook.

    Parameters
    ----------
    comment_id:
        The Facebook comment ID to reply to.
    reply_text:
        The text to post as a reply.

    Raises
    ------
    httpx.HTTPStatusError
        When the Graph API returns a non-2xx status.
    """
    fb = settings.facebook
    url = (
        f"{fb.graph_api_base_url}"
        f"/{fb.graph_api_version}"
        f"/{comment_id}/comments"
    )

    payload = {
        "message": reply_text,
        "access_token": settings.fb_token,
    }

    async with httpx.AsyncClient(timeout=settings.facebook.request_timeout) as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()
