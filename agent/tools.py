from datetime import datetime
import requests, json
from agent.strava_api import create_strava_post
# Configure OAuth2 access token for authorization: strava_oauth
date = datetime.now().isoformat()

data = {
    "name": "11/9",
    "type": "Run",
    "start_date_local": date,
    "elapsed_time": 3600,
    "private": True,
    "description": "Something light",
    "distance": 100000,
}

def strava_post(data):
    create_strava_post(data)