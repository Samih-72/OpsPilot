import pandas as pd

def get_daily_order_summary(orders_df=None):
    if orders_df is None:
        df = pd.read_csv("data/orders.csv")
    else:
        df = orders_df.copy()

    df["order_date"] = pd.to_datetime(
        df["order_date"], errors="coerce"
    ).dt.date

    daily_orders = df.dropna(subset=["order_date"]).groupby(
        "order_date"
    ).size().sort_index()

    if len(daily_orders) < 2:
        return {
            "report_date": "N/A",
            "orders": 0,
            "previous_orders": 0,
            "change": 0
        }

    latest_date = daily_orders.index[-1]
    latest_orders = int(daily_orders.iloc[-1])
    previous_orders = int(daily_orders.iloc[-2])
    change = latest_orders - previous_orders

    return {
        "report_date": str(latest_date),
        "orders": latest_orders,
        "previous_orders": previous_orders,
        "change": change
    }

def get_daily_collection_summary():
    df=pd.read_csv("data/payments.csv")
    successful = df[df["payment_status"]=="Success"]
    daily_collections=successful.groupby("payment_date")["amount_paid"].sum()
    latest_date=daily_collections.index[-1]
    latest_collection=round(float(daily_collections.iloc[-1]),2)
    previous_collection = round(float(daily_collections.iloc[-2]), 2)
    change = round(latest_collection - previous_collection, 2)
    return {
        "report_date": latest_date,
        "successful_collections": latest_collection,
        "previous_collections": previous_collection,
        "change": change
    }


def get_daily_refund_summary():
    # Load the payments spreadsheet
    df = pd.read_csv("data/payments.csv")

    # Convert refund amounts to numbers
    df["refund_amount"] = pd.to_numeric(
        df["refund_amount"], errors="coerce"
    ).fillna(0)

    # Group refunds by payment date and add them
    daily_refunds = df.groupby("payment_date")["refund_amount"].sum()

    # Get the latest date and its refund total
    latest_date = daily_refunds.index[-1]
    latest_refunds = round(float(daily_refunds.iloc[-1]), 2)

    # Get the previous available date's refund total
    previous_refunds = round(float(daily_refunds.iloc[-2]), 2)

    # Compare the two dates
    change = round(latest_refunds - previous_refunds, 2)

    return {
        "report_date": latest_date,
        "refunds": latest_refunds,
        "previous_refunds": previous_refunds,
        "change": change
    }
    

def get_daily_shipping_summary():
    # Load the shipments spreadsheet
    df = pd.read_csv("data/shipments.csv")

    # Keep rows that have a dispatch date
    df = df.dropna(subset=["dispatch_date"])

    # Convert the delay flag into a number
    df["delayed_flag"] = pd.to_numeric(
        df["delayed_flag"], errors="coerce"
    )

    # Count all shipments dispatched on each date
    daily_shipments = df.groupby("dispatch_date").size()

    # Count delayed shipments dispatched on each date
    delayed = df[df["delayed_flag"] == 1]
    daily_delayed = delayed.groupby("dispatch_date").size()

    # Get the latest date with shipment records
    latest_date = daily_shipments.index[-1]

    # Get shipment counts for that date
    total = int(daily_shipments.loc[latest_date])
    delayed_count = int(daily_delayed.get(latest_date, 0))

    # Calculate the delay percentage
    delay_rate = round(delayed_count / total * 100, 2)

    return {
        "report_date": latest_date,
        "total_shipments": total,
        "delayed_shipments": delayed_count,
        "delay_rate_pct": delay_rate
    }


def get_daily_business_briefing(orders_df=None):
    orders = get_daily_order_summary(orders_df=orders_df)
    collections = get_daily_collection_summary()
    refunds = get_daily_refund_summary()
    shipping = get_daily_shipping_summary()

    return {
        "report_date": orders["report_date"],
        "orders": orders,
        "collections": collections,
        "refunds": refunds,
        "shipping": shipping
    }

