import requests
import os
import time
import random

while True:
	row = f"{random.random()},{random.random()},{random.random()},{random.uniform(93,99)},{random.randint(0,1)}"
	requests.post("http://localhost:8000/data", { "body": row })