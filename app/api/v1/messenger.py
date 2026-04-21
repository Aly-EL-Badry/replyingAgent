from fastapi import APIRouter, Request, BackgroundTasks
from fastapi.responses import Response

from app.core.settings_secrets import secrets

from app.features.messenger.service import reply

router = APIRouter(prefix="/messenger", tags=["Messenger"])


@router.get("/")
async def verify(request: Request):
    """Handle the Facebook webhook verification challenge for the Messenger subscription."""
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == secrets.fb_verify_token and challenge:
        print("MESSENGER_WEBHOOK_VERIFIED")
        return Response(content=challenge, media_type="text/plain")

    return Response(content="Verification failed", status_code=403)


@router.post("/")
async def listener(request: Request, background_tasks: BackgroundTasks):
    """Receive incoming Messenger events and dispatch reply tasks in the background."""
    data = await request.json()
    await reply(data, background_tasks)
    return {"status": "ok"}
