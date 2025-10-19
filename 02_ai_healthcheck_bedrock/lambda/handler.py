import os, json, uuid, boto3

region = os.getenv("REGION", "us-east-1")
table_name = os.environ["RESULTS_TABLE"]
model_id = os.getenv("MODEL_ID", "amazon.titan-text-lite-v1")
use_mock = os.getenv("USE_MOCK_BEDROCK", "false").lower() == "true"

dynamodb = boto3.resource("dynamodb", region_name=region)
table = dynamodb.Table(table_name)
bedrock = boto3.client("bedrock-runtime", region_name=region)

def handler(event, context):
    body = json.loads(event.get("body", "{}"))
    text = body.get("text", "")
    print(f"Text received: {text}")

    if use_mock:
        sentiment = "positive" if "good" in text.lower() else "neutral"
    else:
        payload = json.dumps({"inputText": text})
        response = bedrock.invoke_model(modelId=model_id, body=payload)
        model_output = json.loads(response["body"].read())
        sentiment = model_output.get("results", [{}])[0].get("outputText", "")

    record = {
        "id": str(uuid.uuid4()),
        "text": text,
        "sentiment": sentiment,
        "model": model_id,
    }
    table.put_item(Item=record)
    return {"statusCode": 200, "body": json.dumps(record)}
