from fastapi import FastAPI
from fastapi.responses import JSONResponse
from .api_client import fetch_depots, fetch_vehicles
from .optimizer import solve_knapsack
from logging_middleware import Log

app = FastAPI()

@app.get("/schedule")
def schedule():
    Log("backend", "info", "route", "Received request for /schedule endpoint")
    try:
        depots = fetch_depots()
        vehicles = fetch_vehicles()
        
        results = []
        for depot in depots:
            depot_id = depot["ID"]
            mechanic_hours = depot["MechanicHours"]
            
            Log("backend", "info", "service", f"Processing depot ID {depot_id}")
            
            solution = solve_knapsack(vehicles, mechanic_hours)
            
            results.append({
                "depot_id": depot_id,
                "mechanic_hours": mechanic_hours,
                "selected_task_ids": solution["selected_task_ids"],
                "total_duration": solution["total_duration"],
                "total_impact": solution["total_impact"]
            })
            
        Log("backend", "info", "route", "Successfully completed /schedule request")
        return {"results": results}
    except Exception as e:
        Log("backend", "error", "route", f"Error in /schedule endpoint: {e}")
        return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})
