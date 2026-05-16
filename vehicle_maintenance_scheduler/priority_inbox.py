import heapq
import json
import requests
from datetime import datetime
from logging_middleware import Log
from logging_middleware.auth import get_access_token

def fetch_and_rank_notifications():
    Log("backend", "info", "service", "Starting notification fetch and rank process")
    
    url = "http://4.224.186.213/evaluation-service/notifications"
    token = get_access_token()
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        notifications = data.get("notifications", [])
        
        Log("backend", "info", "service", f"Successfully fetched {len(notifications)} notifications")
    except Exception as e:
        Log("backend", "error", "service", f"Failed to fetch notifications: {e}")
        return []

    priority_map = {
        "Placement": 3,
        "Result": 2,
        "Event": 1
    }
    
    top_notifications = []
    current_time = datetime.now()
    
    for i, notif in enumerate(notifications):
        notif_type = notif.get("type", "Event")
        base_score = priority_map.get(notif_type, 0)
        
        created_at_str = notif.get("createdAt", current_time.isoformat())
        
        try:
            created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
            time_diff = (current_time.astimezone() - created_at).total_seconds()
            recency_score = max(0, 1000000 - time_diff) / 1000000 
        except Exception:
            Log("backend", "warn", "utils", "Error parsing date")
            recency_score = 0
            
        final_score = base_score + recency_score
        
        notif_id = notif.get("id") or notif.get("ID") or i
        if len(top_notifications) < 10:
            heapq.heappush(top_notifications, (final_score, notif_id, notif))
        else:
            heapq.heappushpop(top_notifications, (final_score, notif_id, notif))
            
    result = []
    while top_notifications:
        score, notif_id, notif_data = heapq.heappop(top_notifications)
        result.append(notif_data)
        
    result.reverse()
    
    Log("backend", "info", "service", "Completed ranking notifications")
    return result

if __name__ == "__main__":
    ranked = fetch_and_rank_notifications()
    print(json.dumps(ranked, indent=2))
