import logging
from models import Analysis, BillStatus
from datetime import datetime

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def process_bill(bill, db):
    """
    Deterministic bill processing:
    - Calculates fraud_score
    - Builds stable details JSON
    - Logs processing steps
    """

    try:
        logger.info(f"Processing bill {bill.id}")

        # Mock line items for demo purposes
        line_items = [
            {"name": "Consultation", "amount": 5000, "compliant": True},
            {"name": "Lab Tests", "amount": 3000, "compliant": True},
            {"name": "Medication", "amount": 1500, "compliant": False},
        ]

        # ---- Totals calculation ----
        subtotal = sum(item["amount"] for item in line_items)
        tax = int(subtotal * 0.1)
        total = subtotal + tax

        fraud_score = 0
        compliance_flags = []

        # ---- Rule 1: Amount thresholds ----
        if total > 50000:
            fraud_score += 30
            compliance_flags.append({
                "code": "HIGH_AMOUNT",
                "message": "Total exceeds 50,000"
            })
            logger.info("Flag applied: HIGH_AMOUNT")

        elif total > 20000:
            fraud_score += 15
            compliance_flags.append({
                "code": "MEDIUM_AMOUNT",
                "message": "Total exceeds 20,000"
            })
            logger.info("Flag applied: MEDIUM_AMOUNT")

        # ---- Rule 2: Non-compliant line items ----
        non_compliant_count = 0
        for item in line_items:
            if not item["compliant"]:
                fraud_score += 10
                non_compliant_count += 1

        if non_compliant_count > 0:
            compliance_flags.append({
                "code": "NON_COMPLIANT_ITEMS",
                "message": f"{non_compliant_count} non-compliant line items"
            })
            logger.info(f"{non_compliant_count} non-compliant items found")

        # ---- Cap fraud score ----
        fraud_score = min(fraud_score, 100)

        # ---- Stable details JSON ----
        details = {
            "line_items": line_items,
            "compliance_flags": compliance_flags,
            "totals": {
                "subtotal": subtotal,
                "tax": tax,
                "total": total
            },
            "progress": 100
        }

        # ---- Save results to Analysis table ----
        analysis = Analysis(
            bill_id=bill.id,
            fraud_score=fraud_score / 100.0,  # Convert to 0-1 range
            summary=f"Analysis completed with fraud score {fraud_score}%",
            details=details,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(analysis)
        
        # Update bill status
        bill.status = BillStatus.COMPLETED
        db.commit()

        logger.info(
            f"Completed bill {bill.id} with fraud score {fraud_score}"
        )

    except Exception as e:
        logger.error(f"Failed processing bill {bill.id}: {e}")
        bill.status = BillStatus.FAILED
        db.commit()
