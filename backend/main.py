import os
import json
from datetime import datetime
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List
from dotenv import load_dotenv

load_dotenv()

from .agents import (
    parse_intent,
    discover_providers,
    rank_providers,
    simulate_booking,
    schedule_followup
)
from .mock_data import SERVICE_PROVIDERS

BOOKINGS_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "bookings.json")

app = FastAPI(title="Service Orchestrator API - Islamabad")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class OrchestrationRequest(BaseModel):
    user_input: str

class BookingRequest(BaseModel):
    provider: dict
    time_slot: str
    service_type: str

class StatusUpdateRequest(BaseModel):
    booking_id: str
    status: str

@app.post("/orchestrate")
def orchestrate(request: OrchestrationRequest):
    """Full pipeline: Parse -> Discover -> Rank"""
    all_logs = []
    
    # 1. Parse Intent
    intent_data = parse_intent(request.user_input)
    all_logs.extend(intent_data["logs"])
    
    service_type = intent_data.get("service_type")
    location = intent_data.get("location")
    
    if not service_type:
        return {
            "success": False,
            "message": "Could not detect service type. Please be more specific.",
            "logs": all_logs
        }
    
    # 2. Discover
    discovery_data = discover_providers(service_type, location, SERVICE_PROVIDERS)
    all_logs.extend(discovery_data["logs"])
    providers = discovery_data["providers"]
    
    if not providers:
        return {
            "success": False,
            "message": f"No {service_type} found in our records.",
            "logs": all_logs
        }
    
    # 3. Rank
    ranking_data = rank_providers(providers)
    all_logs.extend(ranking_data["logs"])
    
    return {
        "success": True,
        "intent": intent_data,
        "providers": ranking_data["ranked"],
        "logs": all_logs
    }

@app.post("/book-service")
def book_service(request: BookingRequest):
    """Booking pipeline: Simulate -> Followup"""
    all_logs = []
    
    # 4. Simulate Booking
    booking_data = simulate_booking(request.provider, request.time_slot, request.service_type)
    all_logs.extend(booking_data["logs"])
    
    booking = booking_data["booking"]
    
    # 5. Schedule Followup
    followup_data = schedule_followup(booking)
    all_logs.extend(followup_data["logs"])
    
    return {
        "success": True,
        "booking": booking,
        "reminder": followup_data["reminder_time"],
        "message": booking_data["confirmation_message"],
        "logs": all_logs
    }

@app.post("/update-status")
def update_status(data: dict = Body(...)):
    booking_id = data.get("booking_id")
    new_status = data.get("status")
    
    valid_statuses = ["confirmed", "provider_notified", "en_route", "completed"]
    if new_status not in valid_statuses:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    all_logs = []
    all_logs.append(f"[FOLLOWUP AGENT] Status update requested: {booking_id} → {new_status}")
    
    try:
        with open(BOOKINGS_FILE, "r") as f:
            bookings = json.load(f)
        
        updated = False
        for b in bookings:
            if b["booking_id"] == booking_id:
                b["status"] = new_status
                b["status_updated_at"] = datetime.now().isoformat()
                updated = True
                all_logs.append(f"[FOLLOWUP AGENT] Booking {booking_id} status → {new_status}")
                break
        
        if updated:
            with open(BOOKINGS_FILE, "w") as f:
                json.dump(bookings, f, indent=4)
            all_logs.append(f"[FOLLOWUP AGENT] bookings.json updated successfully")
        
        return {
            "success": updated,
            "booking_id": booking_id,
            "new_status": new_status,
            "logs": all_logs
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/providers")
def get_all_providers():
    return SERVICE_PROVIDERS

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

app.mount("/", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "..", "frontend"), html=True), name="frontend")