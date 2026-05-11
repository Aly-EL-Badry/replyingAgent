def ingest_data(data: dict) -> list[tuple[str, str]]:
    events = []
    print(f"Received Messenger Webhook Data: {data}")

    for entry in data.get("entry", []):
        for messaging_event in entry.get("messaging", []):
            # Skip echo / page-sent messages
            if messaging_event.get("message", {}).get("is_echo"):
                sender_id = messaging_event.get("sender", {}).get("id", "unknown")
                print(f"Skipping echo message from sender (id={sender_id})")
                continue

            if "reaction" in messaging_event:
                print("Skipping messenger reaction event.")
                continue

            sender_psid: str = messaging_event.get("sender", {}).get("id", "")
            message_text: str = messaging_event.get("message", {}).get("text", "")

            if sender_psid and message_text:
                events.append((sender_psid, message_text))

    return events
