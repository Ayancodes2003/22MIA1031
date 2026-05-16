import requests
from logging_middleware import Log
from logging_middleware.auth import get_access_token

def fetch_depots():
    Log("backend", "info", "service", "Fetching depots from Affordmed API")
    url = "http://4.224.186.213/evaluation-service/depots"
    token = get_access_token()
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        Log("backend", "info", "service", "Successfully fetched depots")
        return data.get("depots", [])
    except Exception as e:
        Log("backend", "error", "service", f"Error fetching depots: {e}")
        raise

def fetch_vehicles():
    Log("backend", "info", "service", "Fetching vehicles from Affordmed API")
    url = "http://4.224.186.213/evaluation-service/vehicles"
    token = get_access_token()
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        Log("backend", "info", "service", "Successfully fetched vehicles")
        return data.get("vehicles", [])
    except Exception as e:
        Log("backend", "error", "service", f"Error fetching vehicles: {e}")
        raise
