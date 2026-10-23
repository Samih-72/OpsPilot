
import pandas as pd
from pathlib import Path

DATA_FILE = Path(__file__).parent / "data" / "payments.csv"



def calculate_money_collected(year=None):
    payments = pd.read_csv(DATA_FILE, parse_dates=["payment_date"])

    successful_payments = payments[
        payments["payment_status"] == "Success"
    ]

    if year is not None:
        successful_payments = successful_payments[
            successful_payments["payment_date"].dt.year == year
        ]

    total_collected = successful_payments["amount_paid"].sum()

    return float(total_collected)




def compare_monthly_collections(year, month, previous_year, previous_month):
    payments = pd.read_csv(DATA_FILE, parse_dates=["payment_date"])

    successful_payments = payments[
        payments["payment_status"] == "Success"
    ].copy()

    current = successful_payments[
        (successful_payments["payment_date"].dt.year == year)
        & (successful_payments["payment_date"].dt.month == month)
    ]["amount_paid"].sum()

    previous = successful_payments[
        (successful_payments["payment_date"].dt.year == previous_year)
        & (successful_payments["payment_date"].dt.month == previous_month)
    ]["amount_paid"].sum()

    if previous == 0:
        percentage_change = None
    else:
        percentage_change = ((current - previous) / previous) * 100

    return {
        "current_month": f"{year}-{month:02d}",
        "current_collections": float(current),
        "previous_month": f"{previous_year}-{previous_month:02d}",
        "previous_collections": float(previous),
        "change": float(current - previous),
        "percentage_change": (
            float(percentage_change)
            if percentage_change is not None
            else None
        ),
    }

def get_payment_overview():
    """Summarize payment attempts, outcomes, collections, refunds, and fees."""
    payments = pd.read_csv(DATA_FILE)

    total_attempts = len(payments)

    statuses = payments["payment_status"].fillna("").str.strip().str.lower()
    successful = statuses == "success"
    failed = statuses == "failed"

    successful_count = int(successful.sum())
    failed_count = int(failed.sum())

    if total_attempts > 0:
        success_rate = (successful_count / total_attempts) * 100
        failure_rate = (failed_count / total_attempts) * 100
    else:
        success_rate = 0.0
        failure_rate = 0.0

    amounts = pd.to_numeric(payments["amount_paid"], errors="coerce").fillna(0)
    refunds = pd.to_numeric(payments["refund_amount"], errors="coerce").fillna(0)
    fees = pd.to_numeric(payments["transaction_fee"], errors="coerce").fillna(0)

    return {
        "total_payment_attempts": total_attempts,
        "successful_payments": successful_count,
        "failed_payments": failed_count,
        "success_rate_pct": round(success_rate, 2),
        "failure_rate_pct": round(failure_rate, 2),
        "gross_successful_collections": round(
            float(amounts[successful].sum()), 2
        ),
        "total_recorded_refunds": round(float(refunds.sum()), 2),
        "total_recorded_transaction_fees": round(float(fees.sum()), 2),
    }

if __name__ == "__main__":
    print("All years:", calculate_money_collected())
    print("Payment overview:", get_payment_overview())

    result = compare_monthly_collections(2025, 2, 2025, 1)
    print(result)
