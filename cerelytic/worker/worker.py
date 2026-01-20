from database import get_db
from models import Bill
from processor import process_bill
from redis_client import dequeue_analysis_job


def main():
    while True:
        bill_id = dequeue_analysis_job()
        if not bill_id:
            continue

        db = next(get_db())
        bill = db.query(Bill).filter(Bill.id == bill_id).first()

        if not bill:
            continue

        bill.status = "PROCESSING"
        db.commit()

        process_bill(bill, db)


if __name__ == "__main__":
    main()
