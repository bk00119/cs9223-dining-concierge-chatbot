import os
import json
import time, datetime
import pathlib
import urllib.parse, urllib.request
import boto3
from decimal import Decimal

YELP_API_KEY = os.getenv("YELP_API_KEY")
OPENSEARCH_URL = os.getenv("OPENSEARCH_EP").rstrip("/")

CITY = "New York City"
CUISINES = ["chinese", "korean", "japanese", "american", "french", "italian", "mexican"]

DATA_DIR = pathlib.Path("../data")

def yelp_search(city, cuisine, limit, offset):
  base = "https://api.yelp.com/v3/businesses/search"
  params = {"location": city, "categories": cuisine, "limit": limit, "offset": offset}
  url = f"{base}?{urllib.parse.urlencode(params)}"
  req = urllib.request.Request(url, headers={"Authorization": f"Bearer {YELP_API_KEY}"})
  try:
    with urllib.request.urlopen(req, timeout=20) as r:
      return json.loads(r.read().decode("utf-8"))
  except urllib.error.HTTPError as e:
    print(f"{cuisine} offset={offset}: {e}")
    return {"businesses": []}

def opensearch_bulk(docs):
  if not OPENSEARCH_URL or not docs: 
    return
  lines = []
  for d in docs:
    lines.append(json.dumps({"index":{"_index":"restaurants","_id":d["restaurantId"]}}))
    lines.append(json.dumps(d))
  body = ("\n".join(lines) + "\n").encode()
  req = urllib.request.Request(f"{OPENSEARCH_URL}/_bulk", data=body, 
                              headers={"Content-Type":"application/x-ndjson"},
                              method="POST")
  with urllib.request.urlopen(req, timeout=30) as r:
    resp = json.loads(r.read().decode("utf-8"))
    if resp.get("errors"):
      raise Exception("OpenSearch bulk upload errors")

def main():
  DATA_DIR.mkdir(parents=True, exist_ok=True)
  dynamodb = boto3.resource("dynamodb").Table("yelp-restaurants")

  totalPut = 0
  for cuisine in CUISINES:
    savedRestaurants = set()
    pages = 4
    for page in range(1, pages+1):
      pageSize = 50  # each cuisine has 200 records (4 pages x 50)
      offset = (page - 1) * pageSize
      
      data = yelp_search(CITY, cuisine, pageSize, offset)
      
      # save raw JSON data
      jsonFile = DATA_DIR / f"nyc_{cuisine}_{page}.json"
      with jsonFile.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
      print(f"{cuisine} page {page}: saved {jsonFile.name}")

      businesses = data.get("businesses", [])
      if not businesses:
        break
      
      # DynamoDB + OpenSearch
      openSearchDocs = []
      for business in businesses:
        restaurantId = business.get("id")
        if not restaurantId or restaurantId in savedRestaurants:
          continue
        savedRestaurants.add(restaurantId)

        location = business.get("location", {})
        coordinates = business.get("coordinates", {})
        item = {
          "restaurantId": restaurantId, # businessId
          "name": business.get("name"),
          "address": ", ".join(location.get("display_address")),
          "coordinates": {
            "latitude": Decimal(str(coordinates.get("latitude"))),
            "longitude": Decimal(str(coordinates.get("longitude")))
          },
          "reviewCount": int(business.get("review_count")),
          "rating": Decimal(str(business.get("rating"))),
          "zipCode": location.get("zip_code"),
          "insertedAtTimestamp": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        }
        
        dynamodb.put_item(Item=item)
        totalPut += 1

        # OpenSearch: restaurantId + cuisine + city
        if OPENSEARCH_URL:
          openSearchDocs.append({
            "restaurantId": restaurantId,
            "cuisine": cuisine,
            "city": location.get("city")
          })

      # OpenSearch bulk upload
      if OPENSEARCH_URL:
        try:
          opensearch_bulk(openSearchDocs)
        except Exception as e:
          print(f"[warn] OpenSearch bulk skipped/failed: {e}")

      # avoid hitting rate limits
      time.sleep(2)

  print(f"done. dynamodb upserts: {totalPut}")

if __name__ == "__main__":
  main()
