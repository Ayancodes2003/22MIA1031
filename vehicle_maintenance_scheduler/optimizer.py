from logging_middleware import Log

def solve_knapsack(tasks, capacity):
    Log("backend", "info", "service", f"Solving knapsack for capacity {capacity} with {len(tasks)} tasks")
    
    n = len(tasks)
    dp = [[0 for _ in range(capacity + 1)] for _ in range(n + 1)]
    
    for i in range(1, n + 1):
        task_duration = tasks[i-1]["Duration"]
        task_impact = tasks[i-1]["Impact"]
        for w in range(1, capacity + 1):
            if task_duration <= w:
                dp[i][w] = max(task_impact + dp[i-1][w - task_duration], dp[i-1][w])
            else:
                dp[i][w] = dp[i-1][w]
                
    total_impact = dp[n][capacity]
    
    w = capacity
    selected_task_ids = []
    total_duration = 0
    
    for i in range(n, 0, -1):
        if total_impact <= 0:
            break
        if total_impact == dp[i-1][w]:
            continue
        else:
            selected_task_ids.append(tasks[i-1]["TaskID"])
            total_impact -= tasks[i-1]["Impact"]
            total_duration += tasks[i-1]["Duration"]
            w -= tasks[i-1]["Duration"]
            
    selected_task_ids.reverse()
    
    Log("backend", "info", "service", f"Knapsack solved: impact {dp[n][capacity]}, duration {total_duration}")
    
    return {
        "selected_task_ids": selected_task_ids,
        "total_duration": total_duration,
        "total_impact": dp[n][capacity]
    }
