import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()
predict_hq_token = os.getenv("PREDICTHQ_TOKEN")

response = requests.get(
    url="https://api.predicthq.com/v1/events/",
    headers={
      "Authorization": f"Bearer {predict_hq_token}",
      "Accept": "application/json"
    },
    params={
        "q": "taylor swift"
    }
)


data = response.json()


with open("ts_evs.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
