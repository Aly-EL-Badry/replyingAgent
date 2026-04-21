def ingest_data(data: dict) -> list[tuple[str, str, str, str]]:
    """
    Parse Facebook webhook data and return a list of
    (comment_id, message, sender_id, sender_name) tuples.
    """
    events = []
    print(f"Received Webhook Data: {data}") 

    for entry in data.get("entry", []):
        page_id = entry.get("id")

        for change in entry.get("changes", []):
            value = change.get("value", {})
            item_type = value.get("item")
            verb = value.get("verb")

            sender = value.get("from", {})
            sender_id = sender.get("id")
            sender_name = sender.get("name", "")
            if sender_id == page_id:
                print(f"Skipping event from page itself (id={sender_id})")
                continue

            if verb == "add":
                if item_type == "comment":
                    comment_id = value.get("comment_id")
                    message = value.get("message")
                    events.append((comment_id, message, sender_id, sender_name))
                elif item_type == "status":
                    post_id = value.get("post_id")
                    message = value.get("message")
                    events.append((post_id, message, sender_id, sender_name))
                    
    return events

