"""
Generates synthetic ice cream cold-chain distribution data for "Melt Risk".
Why synthetic? No downloads, no broken Kaggle links, fully reproducible, free forever.
Models: products (with shelf life & melt-sensitivity), cold storage warehouses,
daily demand/orders, current inventory, and shipments (with transit delays that
matter a LOT more here because the product melts).
"""
import pandas as pd
import numpy as np
from faker import Faker
from datetime import datetime, timedelta
import random
import os

fake = Faker()
random.seed(42)
np.random.seed(42)

OUT_DIR = "raw"
os.makedirs(OUT_DIR, exist_ok=True)

# ---- Dimension: Products (ice cream SKUs) ----
FLAVORS = ["Vanilla Bean", "Belgian Chocolate", "Mango Swirl", "Strawberry Ripple",
           "Salted Caramel", "Pistachio", "Cookies & Cream", "Mint Choc Chip",
           "Butterscotch", "Black Currant"]
FORMATS = ["Tub 500ml", "Family Pack 1L", "Cone", "Stick Bar", "Mini Cup 100ml"]

N_PRODUCTS = 22
products = []
for i in range(1, N_PRODUCTS + 1):
    flavor = random.choice(FLAVORS)
    fmt = random.choice(FORMATS)
    products.append({
        "product_id": f"IC{i:03d}",
        "product_name": f"{flavor} {fmt}",
        "format": fmt,
        "shelf_life_days_frozen": random.choice([90, 120, 180, 270]),
        "melt_tolerance_hours": round(random.uniform(2.0, 8.0), 1),
        "unit_cost": round(random.uniform(1.2, 6.5), 2),
    })
products_df = pd.DataFrame(products)
products_df.to_csv(f"{OUT_DIR}/products.csv", index=False)

# ---- Dimension: Cold storage warehouses ----
WAREHOUSES = [
    ("CW01", "Mumbai Cold Hub", "West"),
    ("CW02", "Delhi Cold Hub", "North"),
    ("CW03", "Bengaluru Cold Hub", "South"),
    ("CW04", "Kolkata Cold Hub", "East"),
    ("CW05", "Bhubaneswar Cold Hub", "East"),
]
warehouses_df = pd.DataFrame(WAREHOUSES, columns=["warehouse_id", "warehouse_name", "region"])
warehouses_df.to_csv(f"{OUT_DIR}/warehouses.csv", index=False)

# ---- Fact: Daily demand/orders (last 180 days, with summer + weekend spikes) ----
START = datetime.today() - timedelta(days=180)
rows = []
for day_offset in range(180):
    date = START + timedelta(days=day_offset)
    month = date.month
    summer_boost = 1.6 if month in (3, 4, 5, 6) else (1.0 if month in (7, 8, 9) else 0.7)
    weekend_boost = 1.35 if date.weekday() in (4, 5, 6) else 1.0
    for p in products:
        for w in WAREHOUSES:
            base = np.random.poisson(lam=18)
            demand = max(0, int(base * summer_boost * weekend_boost + np.random.normal(0, 3)))
            if demand == 0:
                continue
            rows.append({
                "order_date": date.strftime("%Y-%m-%d"),
                "product_id": p["product_id"],
                "warehouse_id": w[0],
                "units_ordered": demand,
                "unit_cost": p["unit_cost"],
            })
orders_df = pd.DataFrame(rows)
orders_df.to_csv(f"{OUT_DIR}/orders.csv", index=False)

# ---- Fact: Current cold storage inventory snapshot ----
inv_rows = []
for p in products:
    for w in WAREHOUSES:
        avg_daily_demand = orders_df[
            (orders_df.product_id == p["product_id"]) & (orders_df.warehouse_id == w[0])
        ]["units_ordered"].mean()
        avg_daily_demand = 0 if pd.isna(avg_daily_demand) else avg_daily_demand
        days_of_cover = random.choice([1, 2, 3, 5, 8, 12, 20])
        stock_on_hand = int(avg_daily_demand * days_of_cover)
        freezer_temp_c = round(random.choice([-20, -19, -18, -18, -18, -16, -14, -10]), 1)
        inv_rows.append({
            "product_id": p["product_id"],
            "warehouse_id": w[0],
            "stock_on_hand": stock_on_hand,
            "reorder_point": int(avg_daily_demand * 5),
            "freezer_temp_c": freezer_temp_c,
            "snapshot_date": datetime.today().strftime("%Y-%m-%d"),
        })
inventory_df = pd.DataFrame(inv_rows)
inventory_df.to_csv(f"{OUT_DIR}/inventory.csv", index=False)

# ---- Fact: Shipments (cold-chain transit - transit delay = melt risk) ----
ship_rows = []
for _ in range(400):
    date = START + timedelta(days=random.randint(0, 179))
    p = random.choice(products)
    w = random.choice(WAREHOUSES)
    planned_hours = random.randint(4, 30)
    delay_hours = np.random.choice([0, 0, 0, 1, 2, 4, 6, 10], p=[0.45, 0.15, 0.1, 0.1, 0.08, 0.06, 0.04, 0.02])
    refrigeration_failure = np.random.choice([0, 1], p=[0.95, 0.05])
    ship_rows.append({
        "shipment_id": fake.uuid4()[:8],
        "product_id": p["product_id"],
        "warehouse_id": w[0],
        "ship_date": date.strftime("%Y-%m-%d"),
        "planned_transit_hours": planned_hours,
        "actual_transit_hours": planned_hours + delay_hours,
        "refrigeration_failure": int(refrigeration_failure),
        "units_shipped": random.randint(50, 500),
    })
shipments_df = pd.DataFrame(ship_rows)
shipments_df.to_csv(f"{OUT_DIR}/shipments.csv", index=False)

print("Generated (Melt Risk - ice cream cold chain):")
print(f"  products.csv    -> {len(products_df)} rows")
print(f"  warehouses.csv  -> {len(warehouses_df)} rows")
print(f"  orders.csv      -> {len(orders_df)} rows")
print(f"  inventory.csv   -> {len(inventory_df)} rows")
print(f"  shipments.csv   -> {len(shipments_df)} rows")
