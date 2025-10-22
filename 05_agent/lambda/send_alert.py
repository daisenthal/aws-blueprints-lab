import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
    """
    Sends an alert (mocked for now).
    Expected input: {"customer_id": "123"}
    """
    logger.info(f"Received event: {json.dumps(event)}")

    customer_id = event.get("customer_id", "unknown")
    message = f"🚨 Alert triggered for customer {customer_id} due to health risk."
    logger.info(message)

    # Here you could integrate SNS, Slack, or EventBridge
    return {"status": "alert_sent", "message": message}
