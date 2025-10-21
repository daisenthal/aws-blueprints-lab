import boto3, json, os, uuid, logging, traceback
from datetime import datetime

logger = logging.getLogger()
logger.setLevel(logging.INFO)

bedrock = boto3.client("bedrock-runtime")
dynamo = boto3.client("dynamodb")

TABLE = os.environ.get("TABLE_NAME")
MODEL_ID = os.environ.get("BEDROCK_MODEL_ID", "anthropic.claude-3-sonnet-20240229-v1:0")

# --- Optional stub tools until you wire real Lambdas ---
def run_tool(tool_name, args):
    if tool_name == "get_customer_metrics":
        return {"customer_id": args.get("customer_id", "123"), "uptime": 99.8, "tickets": 2, "nps": 87}
    elif tool_name == "summarize_metrics":
        m = args.get("metrics", {})
        return f"Customer {m.get('customer_id')} uptime {m.get('uptime')}%, NPS {m.get('nps')}."
    elif tool_name == "send_alert":
        return f"Alert sent for customer {args.get('customer_id','123')}."
    else:
        return f"Unknown tool {tool_name}"

def save_state(session_id, history):
    if not TABLE:
        return
    try:
        dynamo.put_item(
            TableName=TABLE,
            Item={
                "session_id": {"S": session_id},
                "timestamp": {"S": datetime.utcnow().isoformat()},
                "conversation": {"S": json.dumps(history)}
            }
        )
    except Exception as e:
        logger.warning(f"Dynamo write failed: {e}")

def handler(event, context):
    try:
        body = json.loads(event.get("body", "{}"))
        goal = body.get("goal", "Analyze customer 123 health")
        session_id = str(uuid.uuid4())
        logger.info(f"Session {session_id} start goal={goal}")

        system_prompt = (
            "You are an intelligent assistant with access to tools:\n"
            "1. get_customer_metrics(customer_id)\n"
            "2. summarize_metrics(metrics_json)\n"
            "3. send_alert(customer_id)\n"
            "Always respond in JSON:\n"
            '{"tool":"<tool_name>","arguments":{...}} or '
            '{"tool":"final_answer","result":"..."}\n'
        )

        history = []
        iteration = 0
        last_result = None
        last_tool = None

        while True:
            iteration += 1
            # ---- Build dynamic prompt ----
            context_snippet = f"""
                User goal: {goal}

                Available tools:
                1. get_customer_metrics(customer_id) - Fetch uptime, NPS, ticket count.
                2. summarize_metrics(metrics_json) - Summarize customer status.
                3. send_alert(customer_id) - Notify support if customer appears at risk.

                State summary:
                Last tool used: {last_tool or 'None'}
                Last result: {json.dumps(last_result) if last_result else 'None'}

                Conversation so far (up to 3 latest steps):
                {json.dumps(history[-3:], indent=2)}

                If you already have enough data, return a final_answer.
                Otherwise, select the next most logical tool.
                """

            prompt = f"{system_prompt}\n{context_snippet}\n\nDecide next tool."

            # ---- Call Bedrock model ----
            response = bedrock.invoke_model(
                modelId=MODEL_ID,
                body=json.dumps({"inputText": prompt}),
                accept="application/json",
                contentType="application/json"
            )

            output = json.loads(response["body"].read())
            raw_text = output.get("results", [{}])[0].get("outputText", "{}")

            try:
                decision = json.loads(raw_text)
            except Exception:
                decision = {"tool": "final_answer", "result": f"Bad JSON: {raw_text}"}

            logger.info(f"Iteration {iteration}: {decision}")

            # ---- Check for completion ----
            if decision.get("tool") == "final_answer":
                history.append({"decision": decision, "result": decision.get("result")})
                save_state(session_id, history)
                return {
                    "statusCode": 200,
                    "body": json.dumps({"session_id": session_id, "result": decision.get("result"), "conversation": history})
                }

            # ---- Execute chosen tool ----
            tool_name = decision.get("tool")
            args = decision.get("arguments", {})
            result = run_tool(tool_name, args)
            history.append({"step": iteration, "decision": decision, "result": result})
            last_result = result

            if iteration >= 8:  # safety stop
                history.append({"warning": "max iterations reached"})
                save_state(session_id, history)
                return {"statusCode": 200, "body": json.dumps({"session_id": session_id, "conversation": history})}

    except Exception as e:
        logger.error("Unhandled exception", exc_info=True)
        return {"statusCode": 500, "body": json.dumps({"error": str(e), "trace": traceback.format_exc()})}
