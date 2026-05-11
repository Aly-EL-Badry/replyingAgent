from __future__ import annotations

from app.graph.nodes._helpers import (
    PRIVATE_REPLY_STUBS,
    PRIVATE_REPLY_STUBS_DEFAULT,
    post_thread_reply,
)
from app.graph.state import CommentState
from app.infrastructure.facebook_client import facebook_client
from app.services.data.product_service  import product_service
from app.services.generator             import private_reply_generator


async def product_details_node(state: CommentState) -> dict:
    language = state.language or "en"

    stub = PRIVATE_REPLY_STUBS.get(language, PRIVATE_REPLY_STUBS_DEFAULT)
    await post_thread_reply(state.comment_id, stub)

    row = await product_service.find_product(state.text)

    if row is None:
        if language == "ar":
            dm_text = "عذراً، لم نتمكن من إيجاد منتج يطابق استفسارك. تواصل معنا مباشرةً للمساعدة."
        else:
            dm_text = (
                "Sorry, we couldn't find a product matching your query. "
                "Please contact us directly and we'll be happy to help!"
            )
    else:
        # Feed structured DB data to LLM so it answers the user's specific question
        product_context = product_service.get_details_dm(row, language)
        augmented = (
            f"Product data from our database:\n{product_context}\n\n"
            f"Customer question: {state.text}\n\n"
            f"Answer the customer's specific question using the product data above. "
            f"Be concise, friendly, and helpful. Reply in {'Arabic' if language == 'ar' else 'English'}."
        )
        dm_text = await private_reply_generator.generate(augmented)

    try:
        await facebook_client.send_messenger_message(state.sender_id, dm_text)
        print(
            f"[product_details_node] DM sent → sender={state.sender_id} "
            f"comment={state.comment_id} found={row is not None}"
        )
    except Exception as exc:
        print(f"[product_details_node] DM failed for sender={state.sender_id}: {exc}")

    return {}
