from fastapi import FastAPI, Request, BackgroundTasks

from src.utils.ingestion import ingest_data
from src.reply.generate import generate_reply
from src.facebook.reply import send_fb_reply

app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.post("/trigger")
async def webhook_listener(request: Request, background_tasks: BackgroundTasks):
    data = await request.json()

    events = ingest_data(data)

    for comment_id, comment_text in events:
        background_tasks.add_task(process_cycle, comment_id, comment_text)

    return {"status": "ok"}


async def process_cycle(comment_id: str, text: str):
    reply_text = await generate_reply(text)
    await send_fb_reply(comment_id, reply_text)
