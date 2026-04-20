from fastapi import APIRouter, BackgroundTasks, Request
from fastapi.responses import Response
import asyncio

from app.core.settings_secrets import secrets
from app.utils.ingestion import ingest_data
from app.reply.generate import generate_reply
from app.facebook.reply import send_fb_reply

router = APIRouter(prefix="/trigger", tags=["Webhook"])


@router.get("")
async def verify_webhook(request: Request):
    # Facebook sends these 3 query params during webhook setup.
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == secrets.fb_verify_token and challenge:
        print("WEBHOOK_VERIFIED")
        return Response(content=challenge, media_type="text/plain")

    return Response(content="Verification failed", status_code=403)


@router.post("")
async def webhook_listener(request: Request, background_tasks: BackgroundTasks):
    data = await request.json()

    events = ingest_data(data)

    for comment_id, comment_text, sender_id, sender_name in events:
        background_tasks.add_task(
            process_cycle, comment_id, comment_text, sender_id, sender_name
        )

    return {"status": "ok"}


async def process_cycle(
    comment_id: str, text: str, sender_id: str, sender_name: str
):
    try:
        reply_text = await generate_reply(text)
        if sender_id:
            reply_text = f"@[{sender_id}] {reply_text}"
        await asyncio.sleep(20)
        await send_fb_reply(comment_id, reply_text)
    except Exception as exc:
        # Keep webhook processing resilient if an external API fails.
        print(f"Failed to process comment {comment_id}: {exc}")
