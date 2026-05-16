import requests
from .auth import get_access_token

def Log(stack, level, package, message):
    token = get_access_token()
    url = "http://4.224.186.213/evaluation-service/logs"
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    payload = {
        "stack": stack,
        "level": level,
        "package": package,
        "message": message
    }
    
    try:
        requests.post(url, json=payload, headers=headers)
    except Exception as e:
        print(e)
