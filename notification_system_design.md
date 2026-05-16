# Notification System Design

## Stage 1
To build a robust notification system we first need to establish a clear set of REST APIs. The primary endpoints will include retrieving notifications marking a specific notification as read marking all notifications as read and filtering them by type. 

For fetching notifications we would use a GET request to `/api/v1/notifications`. A successful response returns a JSON array of notification objects each containing an ID type message and read status. To filter by type we can append a query parameter like `?type=Placement`.

Marking a single notification as read requires a PATCH request to `/api/v1/notifications/{id}/read` while marking all as read would use a POST request to `/api/v1/notifications/read-all`. Both operations should return a 200 OK status confirming the action.

For real time delivery Server Sent Events offer a lightweight and efficient approach for one way communication from the server to the client. The client opens a connection via GET `/api/v1/notifications/stream` and the server pushes new events as they occur ensuring immediate delivery without the overhead of WebSockets. All requests must include an `Authorization: Bearer <token>` header for security.

## Stage 2
For the database I strongly recommend PostgreSQL due to its reliability ACID compliance and support for JSONB data types which is useful for flexible notification payloads. 

The schema will involve three main tables. The `students` table will store core user information. The `notifications` table acts as the central repository for messages containing the content type and creation timestamp. Finally the `notification_recipients` table creates a many to many relationship linking students to notifications and tracking the individual `is_read` status for each recipient. 

To ensure fast lookups we must index the foreign keys in the `notification_recipients` table. As the system scales we can implement table partitioning on the `notifications` table based on the creation date. This allows older data to be archived or queried separately keeping the active dataset small and responsive.

## Stage 3
The provided SQL query searching for unread notifications for a specific student ordered by creation date is likely slow because it performs a sequential scan. Without a proper index the database engine must check every row in the table to find matching records. 

To resolve this we should create a composite index on `studentID` `isRead` and `createdAt`. This allows the database to quickly locate the specific student filter the unread items and return them already sorted by date drastically reducing the execution time.

It is important to avoid indexing every single column. Excessive indexes consume significant disk space and slow down write operations like INSERTs and UPDATEs because the database must update the index tree for every change. 

To find students who received Placement notifications in the last seven days we can use the following query:
```sql
SELECT DISTINCT studentID 
FROM notification_recipients nr
JOIN notifications n ON nr.notificationID = n.id
WHERE n.type = 'Placement' 
AND n.createdAt >= NOW() - INTERVAL '7 days';
```

## Stage 4
To handle high traffic and improve performance we can introduce several optimizations. Redis caching is excellent for storing frequently accessed data like the unread notification count. Instead of querying the database every time a user loads the page the application retrieves the count from memory providing near instant responses. The trade off is that cache invalidation can be complex and there is a slight risk of stale data.

Implementing cursor pagination rather than offset pagination ensures stable performance even when dealing with millions of records. Cursor pagination avoids scanning and skipping rows making it incredibly efficient for infinite scrolling interfaces. 

Using read replicas allows us to distribute the read heavy workload across multiple database instances preventing the primary database from becoming a bottleneck. The primary database handles writes while the replicas serve read requests. The main trade off here is eventual consistency as replicas might have a slight delay in reflecting the latest writes. 

## Stage 5
The original `notify_all` approach is prone to failures and performance bottlenecks if executed synchronously. A better design involves decoupling the process using a message queue like RabbitMQ or Kafka. 

When a mass notification is triggered the system first writes the core notification to the database. It then publishes a single event to the message queue. Worker processes consume this event and handle the heavy lifting of generating entries in the `notification_recipients` table and sending out real time alerts. 

This asynchronous approach ensures the main application thread is not blocked. We also implement retries and a dead letter queue to handle transient failures ensuring no messages are lost. Idempotency keys must be used to guarantee that a user does not receive the same notification twice if a worker process crashes and restarts.

```python
def publish_mass_notification(notification_data):
    notification_id = db.insert_notification(notification_data)
    message_queue.publish(
        topic="notifications.mass",
        payload={"notification_id": notification_id},
        idempotency_key=generate_uuid()
    )
    return {"status": "processing"}

def notification_worker(message):
    try:
        if db.is_processed(message.idempotency_key):
            return
        
        notification = db.get_notification(message.notification_id)
        students = db.get_all_active_students()
        
        db.bulk_insert_recipients(notification.id, students)
        real_time_service.broadcast(notification)
        
        db.mark_processed(message.idempotency_key)
    except Exception as e:
        message_queue.nack_and_retry(message)
```

## Stage 6
```python
import heapq
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
    
    for notif in notifications:
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
        
        if len(top_notifications) < 10:
            heapq.heappush(top_notifications, (final_score, notif["id"], notif))
        else:
            heapq.heappushpop(top_notifications, (final_score, notif["id"], notif))
            
    result = []
    while top_notifications:
        score, notif_id, notif_data = heapq.heappop(top_notifications)
        result.append(notif_data)
        
    result.reverse()
    
    Log("backend", "info", "service", "Completed ranking notifications")
    return result

if __name__ == "__main__":
    ranked = fetch_and_rank_notifications()
    print(ranked)
```
