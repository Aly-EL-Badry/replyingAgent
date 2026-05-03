"""
test_graph.py
-------------
Runs the comment-processing LangGraph pipeline locally and prints
every step to the terminal.

Facebook API calls (post_reply, send_messenger_message) are patched
with simple print stubs so no real HTTP requests are made.

Usage:
    pipenv run python test_graph.py
"""

import asyncio
import sys
import uuid
from unittest.mock import patch

# Force UTF-8 output on Windows terminals
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]

# ── Separator helpers ─────────────────────────────────────────────────────────
SEP  = "-" * 60
SEP2 = "=" * 60

def header(title: str) -> None:
    print(f"\n{SEP2}\n  {title}\n{SEP2}")

def section(title: str) -> None:
    print(f"\n{SEP}\n  {title}\n{SEP}")


# ── Test cases ────────────────────────────────────────────────────────────────
TEST_CASES = [
    {
        "label":     "Public comment (EN)",
        "comment_id": str(uuid.uuid4()),
        "text":      "Hey! What are your delivery options?",
        "sender_id": "user_111",
    },
    {
        "label":     "Private comment (should DM via Messenger)",
        "comment_id": str(uuid.uuid4()),
        "text":      "I'd like to know my order status privately please.",
        "sender_id": "user_222",
    },
    {
        "label":     "Arabic comment",
        "comment_id": str(uuid.uuid4()),
        "text":      "ما هي أوقات عمل المتجر؟",
        "sender_id": "user_333",
    },
]


# ── Mock stubs ────────────────────────────────────────────────────────────────
async def mock_post_reply(self, comment_id: str, reply_text: str) -> dict:
    print(f"  [FACEBOOK] post_reply(comment_id={comment_id!r})")
    print(f"     reply -> {reply_text!r}")
    return {"id": "mock_reply_id"}


async def mock_send_messenger_message(self, recipient_id: str, text: str) -> dict:
    print(f"  [MESSENGER] send_messenger_message(recipient={recipient_id!r})")
    print(f"     message -> {text!r}")
    return {"recipient_id": recipient_id, "message_id": "mock_msg_id"}


# ── Runner ────────────────────────────────────────────────────────────────────
async def run_test(case: dict, graph) -> None:
    from app.graph.state import CommentState
    from langchain_core.runnables import RunnableConfig

    section(case["label"])
    print(f"  comment_id : {case['comment_id']}")
    print(f"  sender_id  : {case['sender_id']}")
    print(f"  text       : {case['text']!r}")
    print()

    state = CommentState(
        comment_id=case["comment_id"],
        text=case["text"],
        sender_id=case["sender_id"],
    )
    config: RunnableConfig = {
        "configurable": {"thread_id": case["comment_id"]}
    }

    try:
        result = await graph.ainvoke(state, config=config)  # type: ignore[arg-type]
        print(f"\n  [OK] Graph completed.")
        print(f"  Final state keys: {list(result.keys()) if isinstance(result, dict) else type(result).__name__}")
    except Exception as exc:
        print(f"\n  [FAIL] Graph raised an exception: {exc}", file=sys.stderr)
        raise


async def main() -> None:
    header("LangGraph Comment Pipeline - Terminal Test")

    # Patch Facebook calls BEFORE importing the graph so the singletons
    # are built with the mocked client already in place.
    with (
        patch(
            "app.infrastructure.facebook_client.FacebookClient.post_reply",
            new=mock_post_reply,
        ),
        patch(
            "app.infrastructure.facebook_client.FacebookClient.send_messenger_message",
            new=mock_send_messenger_message,
        ),
    ):
        # Import here so the module-level comment_graph singleton is built
        # inside the patch context.
        from app.graph.builder import comment_graph  # noqa: PLC0415

        graph = comment_graph.graph

        for case in TEST_CASES:
            await run_test(case, graph)

    header("All tests finished")


if __name__ == "__main__":
    asyncio.run(main())
