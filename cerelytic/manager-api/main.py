from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, List

from database import SessionLocal, engine, Base
from models import User, Bill, BillStatus
from schemas import BillCreate, BillWithAnalysisResponse, HealthResponse
from redis_client import enqueue_analysis_job

# ---------------- APP ----------------
app = FastAPI(title="Cerelytic Manager API", version="1.0.0")

# ---------------- CORS ----------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],  # allows x-user-id
)

# ---------------- DB ----------------
Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------- USER ----------------
def ensure_demo_user(db: Session):
    user = db.query(User).filter(User.id == "demo-user").first()
    if not user:
        user = User(id="demo-user")
        db.add(user)
        db.commit()


def get_user_id(x_user_id: str = Header(...)):
    if not x_user_id.strip():
        raise HTTPException(status_code=400, detail="X-User-Id header required")
    return x_user_id


# ---------------- POST /bills ----------------
@app.post("/bills", response_model=BillWithAnalysisResponse)
def create_bill(
    payload: BillCreate,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_user_id),
):
    ensure_demo_user(db)

    bill = Bill(
        user_id=user_id,
        status=BillStatus.QUEUED,
        file_url=payload.file_url,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    db.add(bill)
    db.commit()
    db.refresh(bill)

    # enqueue worker job
    enqueue_analysis_job(bill.id)

    return bill


# ---------------- GET /bills ----------------
@app.get("/bills", response_model=List[BillWithAnalysisResponse])
def list_bills(
    status_filter: Optional[BillStatus] = None,
    limit: int = 10,
    offset: int = 0,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
):
    query = db.query(Bill).filter(Bill.user_id == user_id)

    if status_filter:
        query = query.filter(Bill.status == status_filter)

    bills = (
        query.order_by(Bill.created_at.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )

    return bills


# ---------------- GET /bills/{id} ----------------
@app.get("/bills/{bill_id}", response_model=BillWithAnalysisResponse)
def get_bill(
    bill_id: int,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
):
    bill = (
        db.query(Bill)
        .filter(Bill.id == bill_id, Bill.user_id == user_id)
        .first()
    )

    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")

    return bill


# ---------------- HEALTH ----------------
@app.get("/healthz", response_model=HealthResponse)
def health_check():
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
    )


# ---------------- MAIN ----------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
