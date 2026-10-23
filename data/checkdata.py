
import pandas as pd

customers = pd.read_csv("data/customers.csv")
products = pd.read_csv("data/products.csv")
orders = pd.read_csv("data/orders.csv")
items = pd.read_csv("data/order_items.csv")
payments = pd.read_csv("data/payments.csv")

checks = [
    (
        "Orders → Customers",
        orders["customer_id"],
        customers["customer_id"],
    ),
    (
        "Order items → Orders",
        items["order_id"],
        orders["order_id"],
    ),
    (
        "Order items → Products",
        items["product_id"],
        products["product_id"],
    ),
    (
        "Payments → Orders",
        payments["order_id"],
        orders["order_id"],
    ),
]

for name, source_ids, target_ids in checks:
    missing = source_ids.notna() & ~source_ids.isin(target_ids)

    print(f"\n{name}")
    print(f"Broken references: {missing.sum()}")

    if missing.any():
        print("Examples:")
        print(source_ids[missing].head(5).tolist())
