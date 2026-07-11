# -*- coding: utf-8 -*-
"""Synthetic data generator for the English portfolio dashboard.

The generator builds data bottom-up from SKU performance to campaign performance
and daily channel performance. It preserves the dashboard schema used by the app.
"""

from datetime import date, timedelta
from pathlib import Path
import random

import numpy as np
import pandas as pd


random.seed(42)
np.random.seed(42)

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

START_DATE = date(2024, 12, 1)
END_DATE = date(2025, 12, 31)
ALL_DATES = pd.date_range(START_DATE, END_DATE, freq="D")
N_DAYS = len(ALL_DATES)

CHANNELS = ["Store Referral", "SMS Marketing", "WeChat Content", "Private Community", "Organic App Traffic"]
CHANNEL_BASE_SHARE = {
    "Store Referral": 0.22,
    "SMS Marketing": 0.13,
    "WeChat Content": 0.15,
    "Private Community": 0.18,
    "Organic App Traffic": 0.32,
}
CHANNEL_CR_MULTIPLIER = {
    "Store Referral": 0.95,
    "SMS Marketing": 1.22,
    "WeChat Content": 1.05,
    "Private Community": 1.38,
    "Organic App Traffic": 0.82,
}

PROMOTIONS = {
    "2024-12-12": (1.9, "Double 12 Mega Sale"),
    "2025-01-20": (1.7, "Lunar New Year Sale"),
    "2025-02-14": (1.3, "Valentine Sale"),
    "2025-03-08": (1.5, "International Women's Day Sale"),
    "2025-04-15": (1.2, "Season Refresh"),
    "2025-05-01": (1.4, "Labor Day Sale"),
    "2025-06-18": (2.4, "618 Mid-Year Sale"),
    "2025-07-15": (1.3, "Summer Refresh Sale"),
    "2025-08-08": (1.4, "Anniversary Warm-Up"),
    "2025-09-09": (1.3, "Autumn Refresh Sale"),
    "2025-10-21": (1.6, "Double 11 Presale"),
    "2025-11-11": (2.8, "Double 11 Peak Sale"),
    "2025-11-12": (1.6, "Double 11 Encore"),
    "2025-12-12": (1.9, "Double 12 Mega Sale"),
}
PROMOTION_DATES = {pd.Timestamp(k): v for k, v in PROMOTIONS.items()}

BRANDS = [
    {"brand": "NorthPeak Athletics", "code": "NPA", "category": "Sports & Outdoor", "brand_tier": "Premium Global", "catalog_size": 90, "price_range": (199, 1299), "traffic_idx": 1.6},
    {"brand": "Strive Sportswear", "code": "SSW", "category": "Sports & Outdoor", "brand_tier": "Premium Global", "catalog_size": 85, "price_range": (189, 1199), "traffic_idx": 1.5},
    {"brand": "CoreMotion Performance", "code": "CMP", "category": "Sports & Outdoor", "brand_tier": "Premium Global", "catalog_size": 55, "price_range": (159, 899), "traffic_idx": 1.1},
    {"brand": "RetroFit Active", "code": "RFA", "category": "Sports & Outdoor", "brand_tier": "Premium Global", "catalog_size": 45, "price_range": (149, 799), "traffic_idx": 0.85},
    {"brand": "AquaPulse", "code": "AQP", "category": "Sports & Outdoor", "brand_tier": "Specialist Global", "catalog_size": 35, "price_range": (99, 599), "traffic_idx": 0.65},
    {"brand": "SummitLane Sports", "code": "SLS", "category": "Sports & Outdoor", "brand_tier": "Premium Domestic", "catalog_size": 70, "price_range": (129, 799), "traffic_idx": 1.2},
    {"brand": "FlexStep", "code": "FLX", "category": "Sports & Outdoor", "brand_tier": "Mass Global", "catalog_size": 60, "price_range": (179, 699), "traffic_idx": 1.0},
    {"brand": "TrailForge", "code": "TRF", "category": "Sports & Outdoor", "brand_tier": "Outdoor Specialist", "catalog_size": 50, "price_range": (159, 899), "traffic_idx": 0.8},
    {"brand": "RangeTrail", "code": "RGT", "category": "Sports & Outdoor", "brand_tier": "Outdoor Specialist", "catalog_size": 40, "price_range": (99, 599), "traffic_idx": 0.6},
    {"brand": "PathQuest", "code": "PQT", "category": "Sports & Outdoor", "brand_tier": "Outdoor Specialist", "catalog_size": 38, "price_range": (89, 549), "traffic_idx": 0.55},
    {"brand": "TerraFlow Outfitters", "code": "TFO", "category": "Sports & Outdoor", "brand_tier": "Outdoor Specialist", "catalog_size": 32, "price_range": (79, 499), "traffic_idx": 0.45},
    {"brand": "StreetArc", "code": "STA", "category": "Footwear", "brand_tier": "Lifestyle Global", "catalog_size": 55, "price_range": (219, 699), "traffic_idx": 1.15},
    {"brand": "Heritage Walk", "code": "HRW", "category": "Footwear", "brand_tier": "Heritage Value", "catalog_size": 45, "price_range": (59, 299), "traffic_idx": 0.95},
    {"brand": "MetroStride", "code": "MTS", "category": "Footwear", "brand_tier": "Mass Domestic", "catalog_size": 60, "price_range": (129, 599), "traffic_idx": 0.9},
    {"brand": "CrimsonWing", "code": "CRW", "category": "Footwear", "brand_tier": "Mass Domestic", "catalog_size": 55, "price_range": (119, 549), "traffic_idx": 0.85},
    {"brand": "UrbanEase", "code": "UBE", "category": "Footwear", "brand_tier": "Mass Domestic", "catalog_size": 42, "price_range": (109, 499), "traffic_idx": 0.6},
    {"brand": "PlainWest", "code": "PLW", "category": "Footwear", "brand_tier": "Emerging Brand", "catalog_size": 35, "price_range": (99, 459), "traffic_idx": 0.55},
    {"brand": "Westward", "code": "WST", "category": "Footwear", "brand_tier": "Emerging Brand", "catalog_size": 30, "price_range": (89, 399), "traffic_idx": 0.45},
    {"brand": "FieldBrook", "code": "FDB", "category": "Footwear", "brand_tier": "Emerging Brand", "catalog_size": 28, "price_range": (79, 359), "traffic_idx": 0.4},
    {"brand": "Comely Step", "code": "CMS", "category": "Footwear", "brand_tier": "Emerging Brand", "catalog_size": 26, "price_range": (69, 329), "traffic_idx": 0.35},
    {"brand": "Zenith Harbor", "code": "ZHB", "category": "Footwear", "brand_tier": "Emerging Brand", "catalog_size": 24, "price_range": (69, 299), "traffic_idx": 0.32},
]

SUBCATEGORIES = {
    "Sports & Outdoor": ["Shell Jacket", "Quick-Dry Tee", "Hiking Shoes", "Training Pants", "Sports Backpack", "Down Jacket", "Training Shoes", "Swimwear", "Yoga Set", "Outdoor Sandals"],
    "Footwear": ["Athleisure Sneakers", "Canvas Sneakers", "Leather Shoes", "Boots", "Sandals", "Skate Shoes", "Running Shoes", "Workwear Shoes"],
}
ADJECTIVES = ["AirLite", "Breeze", "SunCore", "Minimal", "CloudSoft", "Featherweight", "Classic", "New Season", "Everyday", "Comfort Fit", "Urban", "Lumen", "Breathable", "GripPro", "CushionFlex", "Trail Ready", "Limited", "Vintage", "TechFeel", "Durable"]


def seasonality_factor(day):
    days_elapsed = (day - pd.Timestamp(START_DATE)).days
    growth = 1.0 + 0.16 * (days_elapsed / N_DAYS)
    weekday_factor = {0: 0.92, 1: 0.90, 2: 0.93, 3: 0.97, 4: 1.08, 5: 1.22, 6: 1.15}[day.weekday()]
    month_factor = {1: 1.08, 2: 0.88, 3: 1.05, 4: 1.00, 5: 1.02, 6: 1.10, 7: 0.95, 8: 1.00, 9: 1.05, 10: 1.08, 11: 1.28, 12: 1.15}[day.month]
    promotion_mult = PROMOTION_DATES[day][0] if day in PROMOTION_DATES else 1.0
    return growth * weekday_factor * month_factor * promotion_mult


def build_catalog(brand_cfg):
    lo, hi = brand_cfg["price_range"]
    rows = []
    for i in range(brand_cfg["catalog_size"]):
        subcategory = random.choice(SUBCATEGORIES[brand_cfg["category"]])
        quality_score = float(np.clip(np.random.beta(5, 3), 0.05, 0.99))
        price_tier = np.random.choice(["Value", "Mid-Market", "Premium"], p=[0.35, 0.45, 0.20])
        if price_tier == "Value":
            price = np.random.uniform(lo, lo + (hi - lo) * 0.30)
        elif price_tier == "Mid-Market":
            price = np.random.uniform(lo + (hi - lo) * 0.30, lo + (hi - lo) * 0.65)
        else:
            price = np.random.uniform(lo + (hi - lo) * 0.65, hi)
        rows.append({
            "sku_id": f"{brand_cfg['code']}-{i + 1:04d}",
            "product_name": f"{brand_cfg['brand']} {ADJECTIVES[i % len(ADJECTIVES)]} {subcategory}",
            "brand": brand_cfg["brand"],
            "category": brand_cfg["category"],
            "subcategory": subcategory,
            "base_price": round(price, 0),
            "quality_score": round(quality_score, 3),
            "price_tier": price_tier,
            "overpriced_flag": np.random.random() < 0.15,
            "weak_listing_flag": np.random.random() < 0.12,
        })
    return pd.DataFrame(rows)


catalogs = {brand["brand"]: build_catalog(brand) for brand in BRANDS}
campaign_types = ["Regular Sale", "Mega Campaign", "Clearance Event", "New Arrival Launch"]
campaign_type_weights = [0.45, 0.20, 0.15, 0.20]
span_days = (END_DATE - START_DATE).days

campaign_rows = []
campaign_id = 1
for brand_cfg in BRANDS:
    n_campaigns = int(np.clip((10 + brand_cfg["traffic_idx"] * 14 + np.random.normal(0, 2)) * (span_days / 365), 6, 34))
    offsets = np.sort(np.random.choice(range(3, span_days - 7), size=n_campaigns, replace=False))
    for offset in offsets:
        start_d = START_DATE + timedelta(days=int(offset))
        duration = random.choice([3, 4, 4, 5, 5, 6, 7])
        end_d = min(start_d + timedelta(days=duration), END_DATE)
        campaign_type = np.random.choice(campaign_types, p=campaign_type_weights)
        promotion_name = ""
        promotion_date = None
        for promo_date, (_, promo_name) in PROMOTION_DATES.items():
            if start_d <= promo_date.date() <= end_d:
                campaign_type = "Mega Campaign"
                promotion_name = promo_name
                promotion_date = promo_date
                break
        campaign_rows.append({
            "campaign_id": f"CAMP{campaign_id:05d}",
            "brand": brand_cfg["brand"],
            "category": brand_cfg["category"],
            "brand_tier": brand_cfg["brand_tier"],
            "traffic_idx": brand_cfg["traffic_idx"],
            "start_date": start_d,
            "end_date": end_d,
            "duration_days": duration,
            "campaign_type": campaign_type,
            "promotion_name": promotion_name,
            "promotion_date": promotion_date,
        })
        campaign_id += 1

campaign_schedule = pd.DataFrame(campaign_rows)
sku_rows = []

for _, campaign in campaign_schedule.iterrows():
    catalog = catalogs[campaign["brand"]]
    sku_lo = max(int(len(catalog) * 0.35), 8)
    sku_hi = max(int(len(catalog) * 0.75), sku_lo + 5)
    sampled = catalog.sample(n=min(random.randint(sku_lo, sku_hi), len(catalog)), replace=False)
    promotion_boost = PROMOTION_DATES[campaign["promotion_date"]][0] if campaign["promotion_name"] else 1.0
    total_campaign_traffic = max(int(3200 * campaign["traffic_idx"] * campaign["duration_days"] * promotion_boost * np.random.normal(1, 0.12)), 300)
    weights = np.random.dirichlet(np.random.uniform(0.3, 0.6, size=len(sampled)))

    for (_, sku), weight in zip(sampled.iterrows(), weights):
        traffic = max(int(total_campaign_traffic * weight), 10)
        ctr = 0.18 + 0.22 * sku["quality_score"]
        if sku["weak_listing_flag"]:
            ctr *= 0.55
        ctr = float(np.clip(ctr * np.random.normal(1, 0.10), 0.04, 0.55))

        base_cr = 0.022 + 0.055 * sku["quality_score"]
        if sku["overpriced_flag"]:
            base_cr *= 0.42
        if sku["weak_listing_flag"]:
            base_cr *= 0.70
        type_cr_mult = {"Regular Sale": 1.0, "Mega Campaign": 1.30, "Clearance Event": 1.45, "New Arrival Launch": 0.65}[campaign["campaign_type"]]
        conversion_rate = float(np.clip(base_cr * type_cr_mult * np.random.normal(1, 0.12), 0.002, 0.32))

        discount_rate = {
            "Regular Sale": np.random.uniform(0.10, 0.30),
            "Mega Campaign": np.random.uniform(0.20, 0.45),
            "Clearance Event": np.random.uniform(0.40, 0.65),
            "New Arrival Launch": np.random.uniform(0.00, 0.15),
        }[campaign["campaign_type"]]
        final_price = sku["base_price"] * (1 - discount_rate)
        if sku["overpriced_flag"]:
            final_price *= 1.12

        orders = int(traffic * conversion_rate)
        gmv = orders * final_price
        stock_quantity = int(np.random.uniform(40, 600) * (1.3 if sku["price_tier"] == "Value" else 0.85))
        sell_through_rate = float(np.clip(orders / max(stock_quantity, 1), 0.0, 1.0))
        refund_rate = 0.075 + (0.035 if sku["overpriced_flag"] else 0) + (0.025 if sku["weak_listing_flag"] else 0)
        refund_rate = float(np.clip(np.random.normal(refund_rate, 0.018), 0.01, 0.30))

        sku_rows.append({
            "campaign_id": campaign["campaign_id"],
            "brand": campaign["brand"],
            "category": sku["category"],
            "subcategory": sku["subcategory"],
            "sku_id": sku["sku_id"],
            "product_name": sku["product_name"],
            "campaign_type": campaign["campaign_type"],
            "start_date": campaign["start_date"].strftime("%Y-%m-%d"),
            "end_date": campaign["end_date"].strftime("%Y-%m-%d"),
            "duration_days": campaign["duration_days"],
            "base_price": sku["base_price"],
            "final_price": round(final_price, 1),
            "discount_rate": round(discount_rate, 3),
            "stock_quantity": stock_quantity,
            "traffic": traffic,
            "click_through_rate": round(ctr, 4),
            "conversion_rate": round(conversion_rate, 4),
            "orders": orders,
            "gmv": round(gmv, 2),
            "sell_through_rate": round(sell_through_rate, 4),
            "refund_rate": round(refund_rate, 4),
            "overpriced_flag": sku["overpriced_flag"],
            "weak_listing_flag": sku["weak_listing_flag"],
        })

sku_performance = pd.DataFrame(sku_rows)

campaign_agg = sku_performance.groupby("campaign_id").agg(
    traffic=("traffic", "sum"),
    orders=("orders", "sum"),
    gmv=("gmv", "sum"),
    refund_rate=("refund_rate", "mean"),
    sku_count=("sku_id", "count"),
).reset_index()
campaign_agg["conversion_rate"] = (campaign_agg["orders"] / campaign_agg["traffic"]).round(4)
campaign_agg["average_order_value"] = (campaign_agg["gmv"] / campaign_agg["orders"].replace(0, np.nan)).round(2)
campaign_agg["new_customer_ratio"] = np.random.uniform(0.15, 0.45, size=len(campaign_agg)).round(4)

brand_campaigns = campaign_schedule.merge(campaign_agg, on="campaign_id", how="left")
brand_campaigns["start_date"] = pd.to_datetime(brand_campaigns["start_date"]).dt.strftime("%Y-%m-%d")
brand_campaigns["end_date"] = pd.to_datetime(brand_campaigns["end_date"]).dt.strftime("%Y-%m-%d")
brand_campaigns = brand_campaigns.drop(columns=["traffic_idx", "promotion_date"])

daily_campaign_gmv = {}
daily_campaign_traffic = {}
for _, campaign in brand_campaigns.iterrows():
    days = pd.date_range(campaign["start_date"], campaign["end_date"], freq="D")
    if len(days) == 0 or pd.isna(campaign["gmv"]):
        continue
    weights = np.array([1.0] + [1.15] * max(len(days) - 2, 0) + ([0.9] if len(days) > 1 else []))[: len(days)]
    weights = weights / weights.sum()
    for day, weight in zip(days, weights):
        daily_campaign_gmv[day] = daily_campaign_gmv.get(day, 0) + campaign["gmv"] * weight
        daily_campaign_traffic[day] = daily_campaign_traffic.get(day, 0) + campaign["traffic"] * weight

daily_rows = []
for day in ALL_DATES:
    sf = seasonality_factor(day)
    campaign_gmv = daily_campaign_gmv.get(day, 0.0)
    campaign_traffic = daily_campaign_traffic.get(day, 0.0)
    baseline_traffic = max(int(9000 * sf * np.random.normal(1, 0.06)), 500)
    baseline_orders = int(baseline_traffic * 0.018 * np.random.normal(1, 0.08))
    baseline_gmv = baseline_orders * 175 * np.random.normal(1, 0.05)
    day_traffic = campaign_traffic + baseline_traffic
    day_gmv = campaign_gmv + max(baseline_gmv, 0)
    est_aov = 170 if campaign_gmv == 0 else (campaign_gmv / max(campaign_traffic * 0.05, 1))
    day_orders = max(int(day_gmv / max(est_aov, 60)), baseline_orders)
    is_promotion_day = day in PROMOTION_DATES
    promotion_name = PROMOTION_DATES[day][1] if is_promotion_day else ""

    channel_traffic = {}
    for channel in CHANNELS:
        channel_traffic[channel] = max(int(day_traffic * CHANNEL_BASE_SHARE[channel] * np.random.normal(1, 0.08)), 30)
    raw_weights = {channel: channel_traffic[channel] * CHANNEL_CR_MULTIPLIER[channel] * np.random.normal(1, 0.06) for channel in CHANNELS}
    weight_sum = sum(raw_weights.values())

    for channel in CHANNELS:
        traffic = channel_traffic[channel]
        order_share = raw_weights[channel] / weight_sum if weight_sum else 1 / len(CHANNELS)
        orders = max(int(day_orders * order_share), 1)
        conversion_rate = float(np.clip(orders / max(traffic, 1), 0.005, 0.30))
        average_order_value = (day_gmv / max(day_orders, 1)) * np.random.normal(1, 0.06)
        refund_rate = float(np.clip(np.random.normal(0.082, 0.014), 0.02, 0.20))
        daily_rows.append({
            "date": day.strftime("%Y-%m-%d"),
            "channel": channel,
            "is_promotion_day": is_promotion_day,
            "promotion_name": promotion_name,
            "traffic": traffic,
            "orders": orders,
            "gmv": round(max(orders * average_order_value, 0), 2),
            "conversion_rate": round(conversion_rate, 4),
            "average_order_value": round(average_order_value, 2),
            "refund_rate": round(refund_rate, 4),
        })

pd.concat(catalogs.values(), ignore_index=True).to_csv(DATA_DIR / "product_catalog.csv", index=False, encoding="utf-8")
sku_performance.to_csv(DATA_DIR / "sku_performance.csv", index=False, encoding="utf-8")
brand_campaigns.to_csv(DATA_DIR / "brand_campaigns.csv", index=False, encoding="utf-8")
pd.DataFrame(daily_rows).to_csv(DATA_DIR / "daily_business.csv", index=False, encoding="utf-8")

print(f"Generated {len(sku_performance):,} SKU-campaign rows.")
print(f"Generated {len(brand_campaigns):,} brand campaigns.")
print("Synthetic data generation complete.")
