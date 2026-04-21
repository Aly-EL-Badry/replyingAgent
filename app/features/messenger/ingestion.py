def ingest_data(data: dict) -> list[tuple[str, str]]:
    """
    Parse a Facebook Messenger webhook payload and return a list of
    (sender_psid, message_text) tuples.

    In a Messenger payload the user ID lives at:
        entry[0].messaging[0].sender.id

    We skip echo events (messages sent by the page itself) and any
    events that carry no text (e.g. attachments, postbacks).
    """
    events = []
    print(f"Received Messenger Webhook Data: {data}")

    for entry in data.get("entry", []):
        for messaging_event in entry.get("messaging", []):
            # Skip echo / page-sent messages
            if messaging_event.get("message", {}).get("is_echo"):
                sender_id = messaging_event.get("sender", {}).get("id", "unknown")
                print(f"Skipping echo message from sender (id={sender_id})")
                continue

            sender_psid: str = messaging_event.get("sender", {}).get("id", "")
            message_text: str = messaging_event.get("message", {}).get("text", "")

            if sender_psid and message_text:
                events.append((sender_psid, message_text))

    return events
