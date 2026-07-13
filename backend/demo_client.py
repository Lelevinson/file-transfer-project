"""
Pretends to be the desktop app: talks to the backend over HTTP.

Start the backend first, in another terminal:
    .venv\\Scripts\\python backend\\app.py
then run this file:
    .venv\\Scripts\\python backend\\demo_client.py
"""

import requests

# the backend's address: loopback IP + the port Flask prints at startup
BASE_URL = "http://127.0.0.1:5000"

print("1) calling the template route, exactly like a browser does")
response = requests.get(f"{BASE_URL}/test/lev/20")
print("   status:", response.status_code)
print("   type  :", response.headers["Content-Type"])
print("   body  :", response.text[:70].strip(), "...")

print("2) calling a route that does not exist")
response = requests.get(f"{BASE_URL}/no-such-route")
print("   status:", response.status_code)
print("   body  :", response.text[:70].strip(), "...")

print("3) POST two users into the backend's database")
for user_id, name in [("1123501", "王小明"), ("1123502", "陳美麗")]:
    response = requests.post(
        f"{BASE_URL}/users",
        data={"id": user_id, "name": name},
    )
    print("   status:", response.status_code, "->", response.json())

print("4) GET the user list back as JSON")
response = requests.get(f"{BASE_URL}/users")
print("   status:", response.status_code)
print("   data  :", response.json())
