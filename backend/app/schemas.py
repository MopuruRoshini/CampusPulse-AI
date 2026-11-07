from pydantic import BaseModel, Field
from typing import Literal

class IncidentCreate(BaseModel):
    title: str = Field(min_length=4, max_length=180)
    description: str = Field(min_length=8)
    category: str = "Other"
    location: str = "Not specified"
    priority: Literal["Critical", "High", "Medium", "Low"] = "Medium"
    reporter: str = "Campus user"

class IncidentUpdate(BaseModel):
    status: str | None = None
    priority: str | None = None
    assigned_to: str | None = None

class ApprovalReview(BaseModel):
    decision: Literal["Approved", "Rejected", "Changes Requested"]
    reviewer: str = Field(min_length=2)
    note: str = ""
