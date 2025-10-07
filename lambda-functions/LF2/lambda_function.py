import os
import json
import urllib.request
import boto3
from botocore.awsrequest import AWSRequest
from botocore.auth import SigV4Auth

sqs = boto3.client("sqs")
ses = boto3.client("ses")
dynamodb = boto3.client("dynamodb")

SQS_URL = os.environ["SQS_URL"].rstrip("/")
OPENSEARCH_URL = os.environ["OPENSEARCH_URL"].rstrip("/")
SENDER = os.environ["EMAIL_SENDER"]

def sigv4_open(url, method="GET", body=None, headers=None, service="es", region=None, timeout=5):
  if headers is None:
    headers = {}
  if body is not None and not isinstance(body, (bytes, bytearray)):
    body = body.encode("utf-8")
  if "Content-Type" not in headers:
    headers["Content-Type"] = "application/json"

  session = boto3.Session()
  creds = session.get_credentials().get_frozen_credentials()
  region = region or session.region_name or "us-east-1"

  awsReq = AWSRequest(method=method, url=url, data=body, headers=headers.copy())
  SigV4Auth(creds, service, region).add_auth(awsReq)

  signedHeaders = dict(awsReq.headers.items())

  req = urllib.request.Request(url, data=body, method=method, headers=signedHeaders)
  return urllib.request.urlopen(req, timeout=timeout)

def get_restaurant_ids(cuisine, location, limit=3):
  url = f"{OPENSEARCH_URL}/restaurants/_search"
  query = {
    "size": limit,
    "query": {
      "bool": {
        "must": [
          {"term": {"cuisine": {"value": cuisine, "case_insensitive": True}}},
          {"term": {"city": {"value": location, "case_insensitive": True}}}  # extra) search by city as well
        ]
      }
    }
    }
  body = json.dumps(query)
  with sigv4_open(url, method="POST", body=body, headers={"Content-Type": "application/json"}) as response:
    data = json.loads(response.read())
  restaurantIds = [h["_id"] for h in data.get("hits",{}).get("hits",[])]
  return restaurantIds

def get_restaurant_details(restaurantIds):
  keys = [{"restaurantId": {"S": _id}} for _id in restaurantIds]
  resp = dynamodb.batch_get_item(
    RequestItems = {
      "yelp-restaurants": {
        "Keys": keys,
        "ProjectionExpression": "restaurantId, #n, address",
        "ExpressionAttributeNames": {"#n": "name"}
      }
    }
  )
  data = resp["Responses"].get("yelp-restaurants", [])
  restaurantDetails = []
  for restaurant in data:
      restaurantDetails.append({
          "restaurantId": restaurant["restaurantId"]["S"],
          "name": restaurant["name"]["S"],
          "address": restaurant["address"]["S"]
      })
  return restaurantDetails

def email_body(req, restaurants=[]):
  header = (
    "Hello! Here are my restaurant suggestions for...\n"
    f"Location: {req.get('Location')}\n"
    f"Cuisine: {req.get('Cuisine')}\n"
    f"Date/Time: {req.get('Date')} {req.get('Time')}\n"
    f"Party Size: {req.get('PartySize')}\n\n"
    "Top picks:\n"
  )
  lines = [f"- {restaurant['name']}, located at {restaurant['address']}" for restaurant in restaurants]
  return header + "\n".join(lines)

def send_email(recipient, subject, body):
  ses.send_email(
    Source=SENDER,
    Destination={"ToAddresses": [recipient]},
    Message={
      "Subject": {"Data": subject},
      "Body": {"Text": {"Data": body}}
    }
  )

def poll_sqs(maxMessages=10, waitTimeSeconds=5):
  response = sqs.receive_message(
    QueueUrl=SQS_URL,
    MaxNumberOfMessages=maxMessages,
    WaitTimeSeconds=waitTimeSeconds
  )
  return response.get("Messages", [])

def lambda_handler(event, context):
  failures = []
  messages = poll_sqs(maxMessages=10, waitTimeSeconds=5)
  for message in messages:
    try:
      payload = json.loads(message["Body"])
      cuisine = payload["Cuisine"]
      location = payload["Location"]
      restaurantIds = get_restaurant_ids(cuisine, location, limit=3)
      if not restaurantIds:
        send_email(payload["Email"], "Dining Concierge Chatbot - No matches found", f"Sorry, I couldn't find any {cuisine} restaurants in {location}.")
        continue
      restaurants = get_restaurant_details(restaurantIds)
      emailBody = email_body(payload, restaurants)
      send_email(payload["Email"], "Dining Concierge Chatbot - Dining Suggestions", emailBody)
      sqs.delete_message(QueueUrl=SQS_URL, ReceiptHandle=message["ReceiptHandle"])
    except Exception as e:
      failures.append({"itemIdentifier": message["MessageId"]})
  return {"batchItemFailures": failures}
