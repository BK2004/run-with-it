from datetime import datetime
import requests, json
from langchain_core.tools import tool
from agent.strava_api import create_strava_post
# Configure OAuth2 access token for authorization: strava_oauth
date = datetime.now().isoformat()

data = {
    "name": "Running",
    "type": "Run",
    "start_date_local": date,
    "elapsed_time": 10,
    "private": True,
    "description": "Created from script",
    "distance": 100000,
}

@tool()
def strava_post(data):
    create_strava_post(data)