from datetime import datetime
import requests, json
from langchain_core.tools import tool
from agent.strava_api import create_strava_post
# Configure OAuth2 access token for authorization: strava_oauth
date = datetime.now().isoformat()

@tool()
def strava_post(name="11/9 run", description=""):
    data = {
        "name": name,
        "type": "Run",
        "start_date_local": date,
        "elapsed_time": 3600,
        "private": True,
        "description": description,
        "distance": 10000,
    }
    create_strava_post(data)