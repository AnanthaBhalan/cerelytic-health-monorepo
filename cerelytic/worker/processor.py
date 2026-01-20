import logging

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

        # ---- Assume bill.line_items exists ----
        # Each item: name, amount, compliant (bool)
        line_items = bill.line_items

        # ---- Totals calculation ----
        subtotal = sum(item.amount for item in line_items)
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
            if not item.compliant:
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
            "line_items": [
                {
                    "name": item.name,
                    "amount": item.amount,
                    "compliant": item.compliant
                }
                for item in line_items
            ],
            "compliance_flags": compliance_flags,
            "totals": {
                "subtotal": subtotal,
                "tax": tax,
                "total": total
            }
        }

        # ---- Save results ----
        bill.fraud_score = fraud_score
        bill.details = details
        bill.status = "COMPLETED"

        db.commit()

        logger.info(
            f"Completed bill {bill.id} with fraud score {fraud_score}"
        )

    except Exception as e:
        logger.error(f"Failed processing bill {bill.id}: {e}")
        bill.status = "FAILED"
        db.commit()
