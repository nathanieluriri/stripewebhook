
import logging
from fastapi import FastAPI, HTTPException, Request
import stripe
import yagmail
import pymongo

import json
from bson import ObjectId

from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()
ONESIGNALAPIKEY = os.getenv("ONESIGNAL")


def send_push_notifications(APIKEY):
    import requests
    import json


    # Define the URL and headers
    url = "https://api.onesignal.com/notifications"
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": f"Basic {APIKEY}"
    }

    # Define the payload
    payload = {
        "app_id": "c0781cfa-4181-49ff-be9a-6c8ac11e5421",
        "contents": {"en": "Push NOtification was triggered by making triggering a payment intent success event"},
        "headings": {"en": "New Order"},
        "sound": "notification_sound",
        "small_icon": "notification_icon",
        "large_icon":"notification_icon",
        "priority": 10,
        "android_channel_id": "8712d174-e24e-409d-8f1e-33144b2c1e33",
        "included_segments": ["All"]
    }

    # Make the POST request
    response = requests.post(url, headers=headers, data=json.dumps(payload))

    # Print the response
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")



send_push_notifications(ONESIGNALAPIKEY)