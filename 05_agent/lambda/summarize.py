import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
    """
    Summarizes customer metrics into a short natural-language statement.
    Expected input: {"metrics": {...}} or {"metrics_json": {...}}
    """
    logger.info(f"Received event: {json.dumps(event)}")

    m = event.get("metrics") or event.get("metrics_json", {})
    customer_id = m.get("customer_id", "unknown")
    uptime = m.get("uptime", "N/A")
    tickets = m.get("tickets", "N/A")
    nps = m.get("nps", "N/A")

    summary = (
        f"Customer {customer_id} has {uptime}% uptime, "
        f"{tickets} open tickets, and NPS {nps}."
    )

    logger.info(f"Summary result: {summary}")
    return {"summary": summary}
