import boto3, json, os, uuid, logging, traceback, re
from datetime import datetime

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# ---- AWS Clients -------------------------------------------------------------
bedrock = boto3.client("bedrock-runtime")
dynamo = boto3.client("dynamodb")
lambda_client = boto3.client("lambda")

# ---- Environment -------------------------------------------------------------
TABLE = os.environ.get("TABLE_NAME")
MODEL_ID = os.environ.get("BEDROCK_MODEL_ID", "anthropic.claude-3-sonnet-20240229-v1:0")
TOOLS = json.loads(os.environ.get("TOOLS", "{}"))  # e.g. {"get_customer_metrics": "arn:aws:lambda:...", ...}

# ==============================================================================
#                            TOOL INVOCATION LAYER
# ==============================================================================
def invoke_tool(tool_name: str, args: dict):
    """
    Invokes the correct Lambda tool dynamically.
    Falls back to mock behavior if ARN missing.
    """
    if tool_name not in TOOLS:
        logger.warning(f"No ARN for tool {tool_name}, using mock fallback.")
        # ---- Mock fallback for local testing ----
        if tool_name == "get_customer_metrics":
            return {"customer_id": args.get("customer_id", "123"), "uptime": 99.8, "tickets": 2, "nps": 87}
        elif tool_name == "summarize_metrics":
            m = args.get("metrics") or args.get("metrics_json", {})
            return f"Customer {m.get('customer_id')} uptime {m.get('uptime')}%, NPS {m.get('nps')}."
        elif tool_name == "send_alert":
            return f"Alert sent for customer {args.get('customer_id','123')}."
        return f"Unknown tool {tool_name}"

    target_arn = TOOLS[tool_name]
    logger.info(f"Invoking Lambda tool {tool_name} ({target_arn}) with args={args}")
    try:
        response = lambda_client.invoke(
            FunctionName=target_arn,
            InvocationType="RequestResponse",
            Payload=json.dumps(args),
        )
        payload = response["Payload"].read()
        result = json.loads(payload)
        logger.info(f"Tool {tool_name} result: {result}")
        return result
    except Exception as e:
        logger.error(f"Error invoking tool {tool_name}: {e}", exc_info=True)
        return {"error": str(e)}


# ==============================================================================
#                            DYNAMO STATE STORAGE
# ==============================================================================
def save_state(session_id, history):
    if not TABLE:
        return
    try:
        dynamo.put_item(
            TableName=TABLE,
            Item={
                "session_id": {"S": session_id},
                "timestamp": {"S": datetime.utcnow().isoformat()},
                "conversation": {"S": json.dumps(history)},
            },
        )
    except Exception as e:
        logger.warning(f"Dynamo write failed: {e}")


# ==============================================================================
#                            BEDROCK INVOCATION
# ==============================================================================
def call_bedrock(prompt: str, model_id: str, system_prompt: str):
    """Claude 3 + Titan compatible Bedrock invocation with debug logs."""
    if model_id.startswith("anthropic.claude-3"):
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "system": system_prompt,
            "messages": [
                {"role": "user", "content": [{"type": "text", "text": prompt}]}
            ],
            "max_tokens": 500,
            "temperature": 0.1,
        }
    elif model_id.startswith("amazon.titan-text"):
        body = {
            "inputText": prompt,
            "textGenerationConfig": {
                "maxTokenCount": 500,
                "temperature": 0.1,
                "topP": 0.9,
            },
        }
    else:
        body = {"inputText": prompt}

    logger.info(f"[DEBUG] Invoking Bedrock model={model_id}")
    logger.info(f"[DEBUG] Request body: {json.dumps(body)[:1500]}")

    response = bedrock.invoke_model(
        modelId=model_id,
        accept="application/json",
        contentType="application/json",
        body=json.dumps(body),
    )
    data = json.loads(response["body"].read())
    logger.info(f"[DEBUG] Raw Bedrock response: {json.dumps(data)[:2000]}")

    try:
        if "content" in data and isinstance(data["content"], list):
            text_out = data["content"][0].get("text", "")
        elif "output" in data:
            text_out = (
                data.get("output", {})
                .get("message", {})
                .get("content", [{}])[0]
                .get("text", "")
            )
        elif "results" in data and data["results"]:
            text_out = data["results"][0].get("outputText", "")
        else:
            text_out = json.dumps(data)
    except Exception as e:
        logger.error(f"[DEBUG] Failed to extract text: {e}")
        text_out = ""

    logger.info(f"[DEBUG] Extracted model text: {text_out.strip()[:500]}")
    return text_out.strip()


# ==============================================================================
#                            MAIN AGENT HANDLER
# ==============================================================================
def handler(event, context):
    try:
        body = json.loads(event.get("body", "{}"))
        goal = body.get("goal", "Analyze customer 123 health")
        session_id = str(uuid.uuid4())
        logger.info(f"Session {session_id} start goal={goal}")

        system_prompt = """
            You are a reasoning agent that decides which tool to call next.

            You must ALWAYS reply in a single line of valid JSON.
            Do not include any code fences, text, or explanations before or after.
            No markdown, no commentary.

            Valid response formats only:
            {"tool": "<tool_name>", "arguments": {...}}
            or
            {"tool": "final_answer", "result": "<summary>"}
            """

        history, iteration, last_result, last_tool = [], 0, None, None

        while True:
            iteration += 1

            context_snippet = f"""
                User goal: {goal}

                Available tools:
                {json.dumps(list(TOOLS.keys()), indent=2)}

                Last tool used: {last_tool or 'None'}
                Last result: {json.dumps(last_result) if last_result else 'None'}

                Recent conversation:
                {json.dumps(history[-3:], indent=2)}

                If you already have enough data, return a final_answer.
                If uptime < 95% or NPS < 50, send an alert before final_answer.”
                If you do not have enough data, select the next most logical tool.
                """
            prompt = f"{system_prompt}\n{context_snippet}\nDecide next tool."

            raw_text = call_bedrock(prompt, MODEL_ID, system_prompt).strip()
            logger.info(f"[DEBUG] Raw model output:\n{raw_text}")

            # ---- Extract JSON decision ----
            json_match = re.search(r"\{.*\}", raw_text, re.DOTALL)
            candidate = json_match.group(0) if json_match else raw_text
            try:
                decision = json.loads(candidate)
                logger.info(f"[DEBUG] Parsed JSON decision: {decision}")
            except Exception as parse_err:
                logger.error(f"[DEBUG] JSON parsing failed: {parse_err}")
                decision = {"tool": "final_answer", "result": f"Bad JSON: {raw_text}"}

            # ---- Stop condition ----
            if decision.get("tool") == "final_answer":
                history.append({"decision": decision, "result": decision.get("result")})
                save_state(session_id, history)
                return {
                    "statusCode": 200,
                    "body": json.dumps(
                        {"session_id": session_id, "result": decision.get("result"), "conversation": history}
                    ),
                }

            # ---- Run chosen tool ----
            tool_name = decision.get("tool")
            args = decision.get("arguments", {})
            result = invoke_tool(tool_name, args)
            history.append({"step": iteration, "decision": decision, "result": result})
            last_tool, last_result = tool_name, result

            # ---- Safety stop ----
            if iteration >= 8:
                history.append({"warning": "max iterations reached"})
                save_state(session_id, history)
                return {
                    "statusCode": 200,
                    "body": json.dumps({"session_id": session_id, "conversation": history}),
                }

    except Exception as e:
        logger.error("Unhandled exception", exc_info=True)
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e), "trace": traceback.format_exc()}),
        }
