import time
import random
from sqlalchemy.orm import Session

from database import SessionLocal
from models import Bill, Analysis, BillStatus


def process_job(job: dict) -> bool:
    """
    Process a job pulled from Redis.
    Job schema:
    {
        job_id,
        bill_id,
        user_id,
        attempt,
        created_at
    }
    """

    bill_id = job.get("bill_id")

    if not bill_id:
        print("Invalid job payload:", job)
        return False

    db: Session = SessionLocal()

    try:
        # Fetch bill from DB
        bill = db.query(Bill).filter(Bill.id == bill_id).first()

        if not bill:
            print(f"Bill {bill_id} not found")
            return False

        # Mark as processing
        bill.status = BillStatus.PROCESSING
        db.commit()

        # Get file_url from DB (not from job)
        file_url = bill.file_url

        print(f"Processing bill {bill_id} from {file_url}")
        time.sleep(3)  # simulate OCR/ML processing

        # Dummy analysis
        fraud_score = round(random.uniform(0.1, 0.9), 2)
        summary = f"Analysis completed for bill {bill_id}. Found {random.randint(1, 10)} issues."

        details = {
            "line_items": [
                {"description": "Medical consultation", "amount": 1500.00, "compliant": True},
                {"description": "Laboratory tests", "amount": 800.00, "compliant": False},
                {"description": "Medication", "amount": 450.00, "compliant": True}
            ],
            "total_amount": 2750.00
        }

        # Create analysis record
        analysis = Analysis(
            bill_id=bill.id,
            fraud_score=fraud_score,
            summary=summary,
            details=details
        )
        db.add(analysis)

        # Mark bill as completed
        bill.status = BillStatus.COMPLETED
        db.commit()

        print(f"Completed processing bill {bill_id}")
        return True

    except Exception as e:
        print(f"Error processing bill {bill_id}: {e}")

        if 'bill' in locals():
            bill.status = BillStatus.FAILED
            db.commit()

        return False

    finally:
        db.close()
