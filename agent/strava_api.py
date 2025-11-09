import requests, json
CLIENT_ID = "184639"
CLIENT_SECRET = "aa97dc975fb30fbd34bd05a322fda6fbcf911368"
CODE = "514b7ad3a709c2cbebd84c3febffe1850093d3e0"

refresh = False
refresh_token = "e187d9a4f9e58608162b3808a79cf5e645505a42"
access_token = "0c0441225294b89757c75f5b9df70feebdb1c76a"

def get_access_refresh():
    tok = requests.post(
        "https://www.strava.com/oauth/token",
        data={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "code": CODE,
            "grant_type": "authorization_code",
        },
    ).json()

    return tok["access_token"], tok["refresh_token"], tok["expires_at"]

def refresh(access_refresh_token):
    r = requests.post(
        "https://www.strava.com/oauth/token",
        data={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type": "refresh_token",
            "refresh_token": access_refresh_token,
        },
    )
    r.raise_for_status()
    j = r.json()
    global refresh_token, access_token
    refresh_token = j["refresh_token"]
    access_token = j["access_token"]
    return j["access_token"], j["refresh_token"], j["expires_at"]

# @tool(parse_docstring=True)
def create_strava_post(data):
    headers = {"Authorization": f"Bearer {access_token}"}
    r = requests.post(
    "https://www.strava.com/api/v3/activities",
    headers=headers,
    data=data,               # IMPORTANT: form-encoded, not JSON
    )
    print(r.status_code, r.text)    # Expect 201 Created
    r.raise_for_status()
    activity = r.json()
    print("Created activity id:", activity["id"])

