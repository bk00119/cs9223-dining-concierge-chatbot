import os
import json
import uuid
from botocore.config import Config
import boto3

BOT_ID = os.environ["BOT_ID"]
BOT_ALIAS_ID = os.environ["BOT_ALIAS_ID"]
LOCALE_ID = "en_US"
AWS_REGION = "us-east-1"

lex = boto3.client("lexv2-runtime")

CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "Content-Type",
  "Access-Control-Allow-Methods": "OPTIONS, POST",
}

def lambda_handler(event, context):
  try:
    body = event.get("body")
    if isinstance(body, str):
      event = json.loads(body)

    msgs = event.get("messages") or []
    if not msgs:
      return {"statusCode": 400, "headers": CORS, "body": json.dumps({"error": "no messages"})}

    text = (msgs[0].get("unstructured") or {}).get("text")
    if not text:
      return {"statusCode": 400, "headers": CORS, "body": json.dumps({"error": "missing text"})}
    
    sessionId = event.get("sessionId") or str(uuid.uuid4())

    res = lex.recognize_text(
      botId=BOT_ID,
      botAliasId=BOT_ALIAS_ID,
      localeId=LOCALE_ID,
      sessionId=sessionId,
      text=text
    )
    msg = [m["content"] for m in res.get("messages", []) if m.get("content")]
    reply = "\n".join(msg) if msg else "Sorry, try again."
    return {
      "statusCode": 200,
      "headers": CORS,
      "body": json.dumps({
        "messages":[{
          "type": "unstructured",
          "unstructured":{"text": reply}
        }]
      })
    }
  except Exception as e:
    return {"statusCode": 500, "headers": CORS, "body": json.dumps({"error":"lex failed","detail":str(e)})}