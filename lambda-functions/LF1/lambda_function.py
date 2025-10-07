import os
import json
import re
import boto3
from datetime import datetime

SQS = boto3.client("sqs")
QUEUE_URL = os.environ.get("QUEUE_URL", "")
CUISINES = ['chinese', 'korean', 'japanese', 'american', 'french', 'italian', 'mexican']
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

def get_slot(slots, name):
  slot = slots.get(name)
  if not slot:
    return None
  if isinstance(slot, dict) and "value" in slot:
    val = slot["value"]
    if isinstance(val, dict) and "interpretedValue" in val:
      return val["interpretedValue"]
  return slot

def validate(slots):
  cuisine = get_slot(slots, "Cuisine")
  location = get_slot(slots, "Location")
  partySize = get_slot(slots, "PartySize")
  date = get_slot(slots, "Date")
  time = get_slot(slots, "Time")
  email = get_slot(slots, "Email")
  
  if not cuisine or cuisine.lower() not in CUISINES:
    return ("Cuisine", f"What cuisine? Choose one of: {', '.join(sorted(CUISINES))}.")
  if not location:
    return ("Location", "Which city?")
  if not partySize or not partySize.isdigit() or int(partySize) <= 0:
    return ("PartySize", "How many people?")
  if not date:
    return ("Date", "What date?")
  if not time:
    return ("Time", "What time?")
  if not email or not EMAIL_RE.match(email):
    return ("Email", "What email should I send the suggestions to?")
  
  return None

def send_to_sqs(data):
  if QUEUE_URL:
    SQS.send_message(
      QueueUrl=QUEUE_URL,
      MessageBody=json.dumps(data)
    )

def response(intentName, slots, dialogType, msg=None, slotToElicit=None, state="InProgress"):
  response = {
    "sessionState": {
      "dialogAction": { "type": dialogType },
      "intent": { "name": intentName, "slots": slots, "state": state }
    }
  }
  if dialogType == "ElicitSlot" and slotToElicit:
    response["sessionState"]["dialogAction"]["slotToElicit"] = slotToElicit
  if msg:
    response["messages"] = [{"contentType": "PlainText", "content": msg}]
  return response

def lambda_handler(event, context):
  intent = event.get("sessionState", {}).get("intent", {}) or {}
  intentName = intent.get("name", "DiningSuggestionIntent")
  slots = intent.get("slots", {}) or {}
  source = event.get("invocationSource")
  
  if source == "DialogCodeHook":
    validation_result = validate(slots)
    if validation_result:
      slot, prompt = validation_result
      return response(intentName, slots, "ElicitSlot", msg=prompt, slotToElicit=slot, state="InProgress")
    return response(intentName, slots, "Delegate", state="InProgress")
  
  if source == "FulfillmentCodeHook":
    data = {
      "Cuisine": get_slot(slots, "Cuisine"),
      "Location": get_slot(slots, "Location"),
      "PartySize": get_slot(slots, "PartySize"),
      "Date": get_slot(slots, "Date"),
      "Time": get_slot(slots, "Time"),
      "Email": get_slot(slots, "Email")
    }
    data["timestamp"] = datetime.utcnow().isoformat()
    send_to_sqs(data)
    msg = (f"Great! I'll send you a list of {data['Cuisine']} restaurants in {data['Location']} "
               f"for {data['PartySize']} on {data['Date']} at {data['Time']}.")
    return response(intentName, slots, "Close", msg=msg, state="Fulfilled")

  return response(intentName, slots, "Close", msg="Sorry, something went wrong.", state="Failed")
