from fastapi import FastAPI
import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()
predict_hq_token = os.getenv("PREDICTHQ_TOKEN")


app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello world"}


# more methods here


@app.get("twsift-test")
async def test():
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

    return {"data": data}