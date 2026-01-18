import time
from fastapi import FastAPI
from datetime import datetime
from sqlalchemy.orm import Session

from schemas import HealthResponse
from database import SessionLocal
from redis_client import dequeue_analysis_job
from models import Bill, Analysis, BillStatus

app = FastAPI(title="Cerelytic Worker API", version="1.0.0")


@app.get("/healthz", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow()
    )


def process_job(job: dict):
    db: Session = SessionLocal()

    try:
        bill_id = job["bill_id"]

        bill = db.query(Bill).filter(Bill.id == bill_id).first()
        if not bill:
            return

        bill.status = BillStatus.PROCESSING
        db.commit()

        # ---- Mock analysis (simulate processing) ----
        time.sleep(2)

        analysis = Analysis(
            bill_id=bill.id,
            fraud_score=0.23,
            summary="Low risk transaction",
            details={"model": "mock-v1"}
        )

        db.add(analysis)

        bill.status = BillStatus.COMPLETED
        db.commit()

        print(f"Processed bill {bill.id}")

    except Exception as e:
        print("Worker error:", e)

    finally:
        db.close()


def worker_loop():
    print("Worker started, waiting for jobs...")
    while True:
        job = dequeue_analysis_job()
        if job:
            process_job(job)
        else:
            time.sleep(1)


if __name__ == "__main__":
    import threading
    import uvicorn

    # Run worker loop in background thread
    threading.Thread(target=worker_loop, daemon=True).start()

    # Run health API
    uvicorn.run(app, host="0.0.0.0", port=8001)
