from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Overview(BaseModel):
    threat_level: str
    active_incidents: int
    events_per_min: int
    ai_confidence: float
    bot_health: str

class Incident(BaseModel):
    id: int
    type: str
    status: str
    timestamp: str

@app.get("/overview", response_model=Overview)
def get_overview():
    return Overview(
        threat_level="ELEVATED",
        active_incidents=3,
        events_per_min=124,
        ai_confidence=0.92,
        bot_health="Healthy"
    )

@app.get("/incidents", response_model=List[Incident])
def get_incidents():
    return [
        Incident(id=1, type="Raid detected", status="contained", timestamp="2026-01-30T12:00:00Z"),
        Incident(id=2, type="Privilege escalation", status="revoked", timestamp="2026-01-30T11:45:00Z"),
        Incident(id=3, type="Canary breach", status="logged", timestamp="2026-01-30T11:30:00Z"),
    ]

@app.post("/operator/lockdown")
def trigger_lockdown():
    # Here you would trigger a real lockdown action
    return {"status": "lockdown triggered"}
