"""Transparent demo workflow. Replace demo executor with live Switch messages once configured."""
import re
from sqlalchemy.orm import Session
from ..models import Incident, Activity, Approval
from ..config import settings

AGENTS = [
 {"id":"pulse","name":"Pulse","role":"Incident Manager","color":"cyan","description":"Classifies reports, prioritizes incidents and coordinates handoffs."},
 {"id":"sherlock","name":"Sherlock","role":"Investigation Agent","color":"violet","description":"Reviews incident history and available diagnostics to identify likely causes."},
 {"id":"fixer","name":"Fixer","role":"Resolution Agent","color":"blue","description":"Prepares safe, actionable troubleshooting plans."},
 {"id":"guardian","name":"Guardian","role":"Verification Agent","color":"green","description":"Checks evidence, risk and approval requirements before closure."},
]

def classify(text: str):
    t=text.lower()
    categories = [("Wi-Fi / Network",["wifi","wi-fi","internet","network","connectivity"]),("Classroom Equipment",["projector","display","computer","lab pc"]),("Electricity",["electricity","power","power cut","outage"]),("Water & Plumbing",["water","leak","plumbing"]),("Maintenance",["maintenance","broken","repair","cleaning"])]
    category=next((name for name,keys in categories if any(k in t for k in keys)),"Other")
    priority="Critical" if any(k in t for k in ["exam in","examination","fire","smoke","electrical shock","emergency"]) else "High" if any(k in t for k in ["urgent","outage","entire block","whole building"]) else "Medium"
    room=re.search(r"(?:room|lab)\s*([A-Za-z0-9-]+)",text,re.I)
    block=re.search(r"([A-Z]{2,5}\s+Block|[A-Z]{2,5}\s+Building|CSE Block)",text,re.I)
    location=", ".join(x for x in [block.group(0) if block else None, f"Room {room.group(1)}" if room else None] if x) or "Not specified"
    return category,priority,location

def log(db, incident, actor, action, detail, simulated):
    db.add(Activity(incident_id=incident.id,actor=actor,action=action,detail=detail,simulated=simulated))

def run_demo_workflow(db: Session, incident: Incident):
    """A deterministic, visibly simulated walkthrough for judges; never claims physical resolution."""
    simulated = settings.app_mode != "live"
    category, priority, location = classify(incident.description)
    incident.category = category if incident.category == "Other" else incident.category
    incident.priority = priority if incident.priority == "Medium" else incident.priority
    if incident.location == "Not specified": incident.location = location
    incident.status = "Investigating"
    log(db,incident,"Pulse","Incident classified",f"{incident.category} · {incident.priority} priority · {incident.location}",simulated)
    log(db,incident,"Pulse","Delegated investigation","Sherlock assigned to review prior incidents and available diagnostics.",simulated)
    log(db,incident,"Sherlock","Investigation summary","No live campus telemetry is connected. Based on the report, check access-point power, uplink status and whether nearby rooms are affected. Findings are hypotheses until evidence is attached.",simulated)
    incident.status = "Solution Proposed"
    log(db,incident,"Fixer","Resolution proposed","1. Confirm whether other devices are affected. 2. Check AP power and uplink indicators. 3. Inspect controller alerts. 4. Escalate to network staff if the AP or uplink is down. Do not reboot shared equipment without IT authorization.",simulated)
    log(db,incident,"Guardian","Safety review completed","The proposal is diagnostic and non-destructive. Any restart or configuration change requires authorized IT approval.",simulated)
    incident.status = "Awaiting Approval"
    approval=Approval(incident_id=incident.id,proposed_action="Authorize IT staff to inspect the access point and, if diagnostics support it, perform an approved restart.",risk_level="Medium")
    db.add(approval)
    log(db,incident,"Guardian","Human approval requested","Waiting for an authorized teammate. The issue is not marked resolved.",simulated)
    db.commit()
    db.refresh(incident)
    return incident
