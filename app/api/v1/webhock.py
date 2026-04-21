from fastapi import APIRouter, Request, BackgroundTasks
from fastapi.responses import Response

from app.core.settings_secrets import secrets

# Import both service functions
from app.features.comments.service import reply as comment_reply
from app.features.messenger.service import reply as messenger_reply

# Use a generic prefix since this handles both
router = APIRouter(prefix="/webhook", tags=["Facebook Webhook"])

@router.get("/")
async def verify(request: Request):
    """Single verification point for all Facebook subscriptions."""
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == secrets.fb_verify_token and challenge:
        print("FACEBOOK_WEBHOOK_VERIFIED")
        return Response(content=challenge, media_type="text/plain")

    return Response(content="Verification failed", status_code=403)

@router.post("/")
async def listener(request: Request, background_tasks: BackgroundTasks):
    """
    Unified listener that detects the type of event and routes 
    it to the correct service (Cortex or Satellitor logic).
    """
    data = await request.json()
    
    # Check if the payload is a Messenger event
    # Messenger events have a 'messaging' key inside the entry
    entry = data.get("entry", [{}])[0]
    
    if "messaging" in entry:
        # Route to Messenger Service
        await messenger_reply(data, background_tasks)
    
    elif "changes" in entry:
        # Route to Comments/Feed Service
        # This handles comments, likes, and mentions
        await comment_reply(data, background_tasks)

    return {"status": "ok"}