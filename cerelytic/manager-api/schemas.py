from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum


class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"


class BillStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# ---------- Input ----------
class BillCreate(BaseModel):
    file_url: str


# ---------- Analysis ----------
class AnalysisResponse(BaseModel):
    id: int
    bill_id: int
    fraud_score: Optional[float]
    summary: Optional[str]
    details: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


# ---------- Bill ----------
class BillResponse(BaseModel):
    id: int
    user_id: str
    status: BillStatus
    file_url: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


# ---------- Bill + Analysis ----------
class BillWithAnalysisResponse(BaseModel):
    id: int
    user_id: str
    status: BillStatus
    file_url: str
    created_at: datetime
    updated_at: datetime
    analysis: Optional[AnalysisResponse] = None

    class Config:
        orm_mode = True


# ---------- Health ----------
class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
