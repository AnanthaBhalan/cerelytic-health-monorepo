from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional

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

@app.on_event("startup")
async def startup_event():
    create_tables()

@app.post("/bills", status_code=status.HTTP_202_ACCEPTED, response_model=dict)
async def create_bill(
    bill_data: BillCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new bill and enqueue it for analysis.
    
    For now, we assume user_id=1 (stubbed auth).
    """
    # TODO: Replace with actual auth - get user_id from JWT token
    user_id = 1
    
    # Create bill record
    db_bill = Bill(
        user_id=user_id,
        file_url=bill_data.file_url,
        status=BillStatus.QUEUED
    )
    db.add(db_bill)
    db.commit()
    db.refresh(db_bill)
    
    # Enqueue analysis job
    job_enqueued = enqueue_analysis_job(db_bill.id, bill_data.file_url)
    if not job_enqueued:
        # Update bill status to failed if job enqueue fails
        db_bill.status = BillStatus.FAILED
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to enqueue analysis job"
        )
    
    return {
        "bill_id": db_bill.id,
        "status": db_bill.status.value
    }

@app.get("/bills/{bill_id}", response_model=BillWithAnalysisResponse)
async def get_bill(
    bill_id: int,
    db: Session = Depends(get_db)
):
    """Get bill status and analysis results if available."""
    bill = db.query(Bill).filter(Bill.id == bill_id).first()
    if not bill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bill not found"
        )
    
    # TODO: Add authorization check - ensure user can only access their own bills
    
    return bill

@app.get("/healthz", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow()
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
