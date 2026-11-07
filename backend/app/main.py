from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import desc
from .config import settings
from .database import Base, engine, get_db, SessionLocal
from .models import Incident, Activity, Approval
from .schemas import IncidentCreate, IncidentUpdate, ApprovalReview
from .agents.workflow import AGENTS, run_demo_workflow
from .integrations.switch_client import SwitchClient

Base.metadata.create_all(bind=engine)
# Seed one clearly documented demo incident for a first-time judge walkthrough.
_seed_db = SessionLocal()
try:
    if _seed_db.query(Incident).count() == 0:
        demo = Incident(title="Wi-Fi outage in CSE Block", description="Wi-Fi unavailable in Room 302 before an online examination.", category="Wi-Fi / Network", location="CSE Block · Room 302", priority="Critical", reporter="Demo student")
        _seed_db.add(demo); _seed_db.commit(); _seed_db.refresh(demo)
        run_demo_workflow(_seed_db, demo)
finally:
    _seed_db.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

app=FastAPI(title="CampusPulse AI API",version="0.1.0",lifespan=lifespan)
app.add_middleware(CORSMiddleware,allow_origins=[settings.frontend_origin,"http://localhost:5173"],allow_credentials=True,allow_methods=["*"],allow_headers=["*"])
switch=SwitchClient()

@app.get("/api/health")
def health(): return {"status":"ok","mode":settings.app_mode,"switch_configured":switch.configured()}

@app.get("/api/overview")
def overview(db:Session=Depends(get_db)):
    incidents=db.query(Incident).all()
    return {"total":len(incidents),"open":sum(i.status not in ["Resolved","Closed"] for i in incidents),"critical":sum(i.priority=="Critical" and i.status not in ["Resolved","Closed"] for i in incidents),"resolved":sum(i.status in ["Resolved","Closed"] for i in incidents),"pending_approvals":db.query(Approval).filter(Approval.status=="Pending").count(),"mode":settings.app_mode,"agents":AGENTS}

@app.get("/api/incidents")
def list_incidents(db:Session=Depends(get_db)):
    return [{"id":i.id,"title":i.title,"description":i.description,"category":i.category,"location":i.location,"priority":i.priority,"status":i.status,"reporter":i.reporter,"assigned_to":i.assigned_to,"created_at":i.created_at,"updated_at":i.updated_at} for i in db.query(Incident).order_by(desc(Incident.created_at)).all()]

@app.post("/api/incidents")
def create_incident(payload:IncidentCreate,db:Session=Depends(get_db)):
    incident=Incident(**payload.model_dump()); db.add(incident); db.commit(); db.refresh(incident)
    run_demo_workflow(db,incident)
    db.refresh(incident)
    return {"id":incident.id,"title":incident.title,"description":incident.description,"category":incident.category,"location":incident.location,"priority":incident.priority,"status":incident.status,"reporter":incident.reporter,"assigned_to":incident.assigned_to,"created_at":incident.created_at}

@app.get("/api/incidents/{incident_id}")
def get_incident(incident_id:int,db:Session=Depends(get_db)):
    i=db.get(Incident,incident_id)
    if not i: raise HTTPException(404,"Incident not found")
    return {"id":i.id,"title":i.title,"description":i.description,"category":i.category,"location":i.location,"priority":i.priority,"status":i.status,"reporter":i.reporter,"assigned_to":i.assigned_to,"events":[{"id":e.id,"actor":e.actor,"action":e.action,"detail":e.detail,"simulated":e.simulated,"created_at":e.created_at} for e in sorted(i.events,key=lambda e:e.created_at)]}

@app.patch("/api/incidents/{incident_id}")
def update_incident(incident_id:int,payload:IncidentUpdate,db:Session=Depends(get_db)):
    i=db.get(Incident,incident_id)
    if not i: raise HTTPException(404,"Incident not found")
    for k,v in payload.model_dump(exclude_none=True).items(): setattr(i,k,v)
    db.add(Activity(incident_id=i.id,actor="Human teammate",action="Incident updated",detail=str(payload.model_dump(exclude_none=True)),simulated=settings.app_mode!="live"))
    db.commit(); db.refresh(i)
    return {"id":i.id,"status":i.status,"priority":i.priority,"assigned_to":i.assigned_to}

@app.delete("/api/incidents/{incident_id}")
def delete_incident(incident_id:int,db:Session=Depends(get_db)):
    i=db.get(Incident,incident_id)
    if not i: raise HTTPException(404,"Incident not found")
    db.delete(i); db.commit(); return {"deleted":True,"id":incident_id}

@app.get("/api/approvals")
def approvals(db:Session=Depends(get_db)):
    return [{"id":a.id,"incident_id":a.incident_id,"incident_title":a.incident.title,"proposed_action":a.proposed_action,"risk_level":a.risk_level,"status":a.status,"reviewer":a.reviewer,"created_at":a.created_at} for a in db.query(Approval).order_by(desc(Approval.created_at)).all()]

@app.post("/api/approvals/{approval_id}/review")
def review_approval(approval_id:int,payload:ApprovalReview,db:Session=Depends(get_db)):
    a=db.get(Approval,approval_id)
    if not a: raise HTTPException(404,"Approval not found")
    if a.status!="Pending": raise HTTPException(409,"Approval already reviewed")
    a.status=payload.decision; a.reviewer=payload.reviewer; a.review_note=payload.note; a.reviewed_at=datetime.now(timezone.utc)
    incident=db.get(Incident,a.incident_id)
    if payload.decision=="Approved":
        incident.status="In Progress"
        detail="Human approved the proposed IT inspection. Physical completion still requires evidence and confirmation."
    elif payload.decision=="Rejected":
        incident.status="Solution Proposed"; detail="Human rejected the proposed action."
    else:
        incident.status="Solution Proposed"; detail="Human requested changes to the proposed action."
    db.add(Activity(incident_id=incident.id,actor=payload.reviewer,action=f"Approval {payload.decision}",detail=detail+ (" "+payload.note if payload.note else ""),simulated=settings.app_mode!="live"))
    db.commit(); return {"id":a.id,"status":a.status,"incident_status":incident.status}

@app.post("/api/incidents/{incident_id}/confirm-resolution")
def confirm_resolution(incident_id:int,reviewer:str, evidence:str,db:Session=Depends(get_db)):
    i=db.get(Incident,incident_id)
    if not i: raise HTTPException(404,"Incident not found")
    if not evidence.strip(): raise HTTPException(400,"Evidence is required")
    i.status="Resolved"
    db.add(Activity(incident_id=i.id,actor=reviewer,action="Resolution confirmed by human",detail=evidence,simulated=settings.app_mode!="live"))
    db.commit(); return {"id":i.id,"status":i.status}

@app.get("/api/agents")
def agents(): return AGENTS

@app.get("/api/integrations/status")
async def integration_status():
    switch_status=await switch.health()
    return {"mode":settings.app_mode,"switch":switch_status,"discord_configured":bool(settings.discord_bot_token),"note":"A healthy Switch server does not by itself prove agent registration, room membership or live message handling."}
