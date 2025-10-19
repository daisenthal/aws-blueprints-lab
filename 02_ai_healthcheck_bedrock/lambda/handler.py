import os
import json
import uuid
import boto3

# Only load dotenv locally
if os.getenv("AWS_EXECUTION_ENV") is None:
    from dotenv import load_dotenv
    load_dotenv()

dynamodb = boto3.resource("dynamodb", region_name=os.getenv("AWS_REGION", "us-east-1"))
table_name = os.environ["RESULTS_TABLE"]
table = dynamodb.Table(table_name)

def handler(event, context):
    body = json.loads(event.get("body", "{}"))
    text = body.get("text", "")

    sentiment = "positive" if "good" in text.lower() else "neutral"

    record = {
        "id": str(uuid.uuid4()),
        "text": text,
        "sentiment": sentiment
    }

    table.put_item(Item=record)

    return {
        "statusCode": 200,
        "body": json.dumps(record)
    }
