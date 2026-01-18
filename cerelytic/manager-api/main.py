from fastapi import FastAPI, Depends, HTTPException, status, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, List

from database import get_db, create_tables
from models import User, Bill, Analysis, BillStatus
from schemas import BillCreate, BillWithAnalysisResponse, HealthResponse
from redis_client import enqueue_analysis_job

app = FastAPI(title="Cerelytic Manager API", version="1.0.0")

# CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Dependency to get user id ----------
def get_user_id(x_user_id: str = Header(...)):
    if not x_user_id.strip():
        raise HTTPException(status_code=400, detail="X-User-Id header required")
    return x_user_id


@app.on_event("startup")
async def startup_event():
    create_tables()


# ---------- POST /bills ----------
@app.post("/bills", status_code=status.HTTP_202_ACCEPTED)
async def create_bill(
    bill_data: BillCreate,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db)
):
    db_bill = Bill(
        user_id=user_id,
        file_url=bill_data.file_url,
        status=BillStatus.QUEUED
    )
    db.add(db_bill)
    db.commit()
    db.refresh(db_bill)

    job_enqueued = enqueue_analysis_job(db_bill.id, user_id)

    if not job_enqueued:
        db_bill.status = BillStatus.FAILED
        db.commit()
        raise HTTPException(
            status_code=500,
            detail="Failed to enqueue analysis job"
        )

    return {
        "bill_id": db_bill.id,
        "status": db_bill.status.value
    }


# ---------- GET /bills ----------
@app.get("/bills", response_model=List[BillWithAnalysisResponse])
async def list_bills(
    status_filter: Optional[BillStatus] = None,
    limit: int = 10,
    offset: int = 0,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db)
):
    query = (
        db.query(Bill)
        .filter(Bill.user_id == user_id)
    )

    if status_filter:
        query = query.filter(Bill.status == status_filter)

    bills = (
        query
        .order_by(Bill.created_at.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )

    return bills


# ---------- GET /bills/{bill_id} ----------
@app.get("/bills/{bill_id}", response_model=BillWithAnalysisResponse)
async def get_bill(
    bill_id: int,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db)
):
    bill = (
        db.query(Bill)
        .filter(Bill.id == bill_id, Bill.user_id == user_id)
        .first()
    )

    if not bill:
        raise HTTPException(
            status_code=404,
            detail="Bill not found"
        )

    return bill


# ---------- Health ----------
@app.get("/healthz", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow()
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
