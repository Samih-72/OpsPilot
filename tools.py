import json
from langchain_core.tools import tool

from analytics import (
    calculate_money_collected,
    compare_monthly_collections,
    get_payment_overview as calculate_payment_overview,
)

import pandas as pd
from pathlib import Path

CUSTOMERS_FILE = Path(__file__).parent / "data" / "customers.csv"

customers_df = pd.read_csv(CUSTOMERS_FILE, dtype={"customer_id": str})


@tool
def get_customer(customer_id: str):
    """Look up a customer by their exact customer ID.

    Use this tool when asked for a customer's profile,
    spending, order count, segment, loyalty tier, or status.
    This is a customer ID, not an order ID.
    """
    customer = customers_df[
        customers_df["customer_id"].str.upper()
        == customer_id.strip().upper()
    ]

    if customer.empty:
        return f"No customer found with ID {customer_id}."

    record = customer.iloc[0]

    return (
        f"Customer ID: {record['customer_id']}\n"
        f"Customer segment: {record['customer_segment']}\n"
        f"Customer status: {record['customer_status']}\n"
        f"Loyalty tier: {record['loyalty_tier']}\n"
        f"Total orders: {record['total_orders']}\n"
        f"Total spend: ₹{record['total_spend']:,.2f}\n"
        f"Average order value: ₹{record['average_order_value']:,.2f}\n"
        f"Preferred payment method: {record['preferred_payment_method']}\n"
        f"Preferred device: {record['preferred_device']}"
    )

@tool
def get_order(order_id: str):
    """Retrieve order details using the order ID."""
    order = orders.get(order_id.upper())

    if order is None:
        return "Order not found"

    customer = order["customer"]
    status = order["status"]
    days_delayed = order["days_delayed"]

    if days_delayed > 0:
        return f"{customer}'s order {order_id.upper()} is {status.lower()} by {days_delayed} days."

    return f"{customer}'s order {order_id.upper()} is {status.lower()}."

@tool
def get_return_policy():
    """retreive the stores return policy"""
    return(
        "Customers can return eligible products within "
        "7 days of delivery. Products must be unused "
        "and in their original packaging. "
        "Refunds are processed after the returned product "
        "is inspected."
    )

@tool
def get_money_collected(year: int = None):
    """Calculate gross successful payment collections.
    Optionally filter by calendar year, such as 2025.
    Refunds are not subtracted from this total.
    """
    total = calculate_money_collected(year)

    if year is not None:
        return (
            f"Gross successful payment collections for {year}: "
            f"₹{total:,.2f}. Refunds are not subtracted."
        )

    return (
        f"Gross successful payment collections across all years: "
        f"₹{total:,.2f}. Refunds are not subtracted."
    )

@tool
def get_monthly_collection_comparison(
    year: int,
    month: int,
    previous_year: int,
    previous_month: int,
):
    """Compare payment collections for two specific months.

Use this tool whenever the user asks to:
- Compare collections between two months.
- Get collections for a specific month.
- Calculate month-over-month collection changes.
- Find the percentage increase or decrease between months.

Example: Compare February 2025 with January 2025.
Use month numbers from 1 to 12.
Refunds are not subtracted.
"""
    if not 1 <= month <= 12 or not 1 <= previous_month <= 12:
        return "Invalid month. Please use a month from 1 to 12."

    result = compare_monthly_collections(
        year, month, previous_year, previous_month
    )

    current = result["current_collections"]
    previous = result["previous_collections"]
    change = result["change"]
    percentage = result["percentage_change"]

    if percentage is None:
        change_text = "Percentage change is unavailable because the previous month's collections are zero."
    else:
        change_text = f"Percentage change: {percentage:.2f}%."

    return (
        f"Collections for {result['current_month']}: ₹{current:,.2f}. "
        f"Collections for {result['previous_month']}: ₹{previous:,.2f}. "
        f"Absolute change: ₹{change:,.2f}. "
        f"{change_text} Refunds are not subtracted."
    )

@tool
def get_payment_health_summary():
    """Retrieve an overview of payment performance.

    Use this tool when asked about payment success or failure rates,
    payment attempts, gross collections, recorded refunds,
    or transaction fees.
    """
    return calculate_payment_overview()



@tool
def analyze_payment_methods() -> str:
    """Analyze payment attempts, failures, and success rates by payment method using payments.csv."""
    try:
        df = pd.read_csv("data/payments.csv")

        required = {"payment_method", "payment_status"}
        if not required.issubset(df.columns):
            return "Missing required columns: payment_method or payment_status."

        df["payment_method"] = (
            df["payment_method"].fillna("Unknown").astype(str)
        )
        df["payment_status"] = (
            df["payment_status"].fillna("Unknown").astype(str).str.strip()
        )

        # Use only recognized statuses to avoid treating pending
        # or uncharged payments as failures.
        df["is_success"] = df["payment_status"].str.lower().eq("success")
        df["is_failed"] = df["payment_status"].str.lower().eq("failed")

        result = df.groupby("payment_method").agg(
            total_attempts=("payment_id", "count"),
            successful_payments=("is_success", "sum"),
            failed_payments=("is_failed", "sum"),
        )

        result["success_rate_pct"] = (
            result["successful_payments"] / result["total_attempts"] * 100
        ).round(2)

        result["failure_rate_pct"] = (
            result["failed_payments"] / result["total_attempts"] * 100
        ).round(2)

        return result.to_string()

    except FileNotFoundError:
        return "Could not find data/payments.csv. Check the dataset path."
    except Exception as e:
        return f"Payment method analysis failed: {e}"

@tool
def analyze_payment_statuses_by_method() -> str:
    """Show payment status counts by payment method to help investigate payment performance."""
    try:
        df = pd.read_csv("data/payments.csv")

        required = {"payment_id", "payment_method", "payment_status"}
        if not required.issubset(df.columns):
            return "Required payment columns are missing."

        result = pd.crosstab(
            df["payment_method"].fillna("Unknown"),
            df["payment_status"].fillna("Unknown"),
            margins=True,
        )

        return result.to_string()

    except FileNotFoundError:
        return "Could not find data/payments.csv."
    except Exception as e:
        return f"Payment status analysis failed: {e}"


@tool
def detect_payment_problems() -> str:
    """Detect payment methods with high recorded failure rates or large failure counts."""
    try:
        df = pd.read_csv("data/payments.csv")

        required = {"payment_id", "payment_method", "payment_status"}
        if not required.issubset(df.columns):
            return "Required payment columns are missing."

        df = df.dropna(subset=["payment_id", "payment_method", "payment_status"])
        df["payment_status"] = df["payment_status"].astype(str).str.strip()
        df["payment_method"] = df["payment_method"].astype(str).str.strip()

        summary = df.groupby("payment_method").agg(
            total_records=("payment_id", "count"),
            failed_records=(
                "payment_status",
                lambda s: s.str.lower().eq("failed").sum(),
            ),
        )

        summary["failure_rate_pct"] = (
            summary["failed_records"] / summary["total_records"] * 100
        ).round(2)

        # Flag methods with at least a 6% recorded failure rate.
        # This is an investigation threshold, not a universal industry benchmark.
        flagged = summary[
            (summary["failure_rate_pct"] >= 6)
            & (summary["failed_records"] > 0)
        ].sort_values(
            ["failure_rate_pct", "failed_records"],
            ascending=False,
        )

        if flagged.empty:
            return "No payment methods crossed the configured investigation threshold."

        return (
            "Payment methods to investigate "
            "(rates use all records, not confirmed checkout attempts):\n\n"
            + flagged.to_string()
            + "\n\nThe dataset does not contain failure reasons. "
            "These patterns identify where to investigate, not the cause."
        )

    except FileNotFoundError:
        return "Could not find data/payments.csv. Check the dataset path."
    except Exception as e:
        return f"Payment problem detection failed: {e}"
ORDERS_FILE = Path(__file__).parent / "data" / "orders.csv"

@tool

def get_total_orders(orders_df=None) -> str:
    """Get the total number of unique orders."""

    try:
        if orders_df is None:
            df = pd.read_csv(ORDERS_FILE)
        else:
            df = orders_df

        if "order_id" not in df.columns:
            return "Cannot count orders: order_id column is missing."

        total = df["order_id"].nunique()

        return f"Total unique orders in the dataset: {total:,}."

    except FileNotFoundError:
        return f"Orders file not found: {ORDERS_FILE}"
    except Exception as e:
        return f"Could not calculate total orders: {e}"
