def ingest_data(data: dict) -> list[tuple[str, str]]:
    """
    Parse the Facebook webhook payload and extract new comment events.

    Returns a list of (comment_id, comment_text) tuples for every
    comment-add event found in the payload.
    """
    events = []
    for entry in data.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            if value.get("item") == "comment" and value.get("verb") == "add":
                comment_id = value.get("comment_id")
                comment_text = value.get("message")
                events.append((comment_id, comment_text))
    return events