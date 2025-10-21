import boto3, json, os, uuid, logging
from datetime import datetime

bedrock = boto3.client("bedrock-runtime")
dynamo = boto3.client("dynamodb")

TABLE = os.environ.get("TABLE_NAME")
MODEL_ID = os.environ.get("BEDROCK_MODEL_ID", "anthropic.claude-3-sonnet-20240229-v1:0")

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# --- Mock Tool Responses ---
def mock_tool_response(tool_name: str, args: dict):
    if tool_name == "get_customer_metrics":
        return {
            "customer_id": args.get("customer_id", "123"),
            "uptime": 99.8,
            "tickets": 1,
            "nps": 87
        }
    elif tool_name == "summarize_metrics":
        m = args.get("metrics", {})
        return f"Customer {m.get('customer_id','123')} uptime {m.get('uptime')}%, NPS {m.get('nps')}."
    elif tool_name == "send_alert":
        return f"Alert triggered for customer {args.get('customer_id','123')}."
    else:
        return f"No mock for {tool_name}"

def save_state(session_id, history):
    if not TABLE:
        return
    dynamo.put_item(
        TableName=TABLE,
        Item={
            "session_id": {"S": session_id},
            "timestamp": {"S": datetime.utcnow().isoformat()},
            "conversation": {"S": json.dumps(history)}
        }
    )

def handler(event, context):
    try:
        body = json.loads(event.get("body", "{}"))
    except Exception:
        body = {}
    goal = body.get("goal", "Analyze customer 123 health")
    session_id = str(uuid.uuid4())
    logger.info(f"Session {session_id} start goal={goal}")

    history = []
    last_tool = None
    iteration = 0

    while True:
        iteration += 1

        # --- Simulated Decision Logic ---
        # We won't call Bedrock yet; just simulate its "thinking"
        if last_tool is None:
            decision = {"tool": "get_customer_metrics", "arguments": {"customer_id": "123"}}

        elif last_tool == "get_customer_metrics":
            # after metrics, call summarize
            decision = {"tool": "summarize_metrics", "arguments": {"metrics": history[-1]["result"]}}

        elif last_tool == "summarize_metrics":
            # after summary, finish with final_answer
            decision = {"tool": "final_answer", "result": history[-1]["result"]}
        
        else:
            decision = {"tool": "final_answer", "result": "Done."}

        tool_name = decision.get("tool")
        logger.info(f"Iteration {iteration}: {decision}")

        # --- Final Answer ---
        if tool_name == "final_answer":
            result = decision.get("result")
            history.append({"step": iteration, "decision": decision, "result": result})
            save_state(session_id, history)
            return {
                "statusCode": 200,
                "body": json.dumps({
                    "session_id": session_id,
                    "result": result,
                    "conversation": history
                })
            }

        # --- Mock Tool Execution ---
        result = mock_tool_response(tool_name, decision.get("arguments", {}))
        history.append({"step": iteration, "decision": decision, "result": result})
        last_tool = tool_name

        # Safety stop
        if iteration > 5:
            history.append({"warning": "loop stop"})
            save_state(session_id, history)
            return {"statusCode": 200, "body": json.dumps({"result": "stopped"})}
