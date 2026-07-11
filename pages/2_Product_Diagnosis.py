# -*- coding: utf-8 -*-
"""Product Diagnosis - SKU segmentation and root-cause signals."""

from pathlib import Path
import sys

import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.append(str(Path(__file__).parent.parent))
from utils import fmt_pct, load_sku_performance


st.set_page_config(page_title="Product Diagnosis", page_icon="🔍", layout="wide")
st.title("🔍 Product Diagnosis")
st.caption("Identify high-traffic, low-conversion SKUs and prioritize root-cause investigation.")

st.info(
    "This page uses a traffic-by-conversion matrix to segment SKUs. The highest-priority group is "
    "high-traffic, low-conversion products because they receive exposure but fail to convert demand."
)

with st.container(border=True):
    st.markdown(
        """
**💡 Why this matters**

Low GMV does not always mean a product should be fixed first. The most urgent opportunities are often
SKUs with high traffic and weak conversion because the platform is already investing exposure in them.
Improving their content, price competitiveness, inventory availability, or refund risk can create faster GMV upside.
"""
    )

sku = load_sku_performance()

col0, col1, col2, col3 = st.columns([1.3, 1, 1, 1])
with col0:
    date_range = st.date_input(
        "Campaign start date",
        value=(sku["start_date"].min(), sku["start_date"].max()),
        min_value=sku["start_date"].min(),
        max_value=sku["start_date"].max(),
    )
with col1:
    category_sel = st.multiselect("Category", sku["category"].unique().tolist(), default=sku["category"].unique().tolist())
with col2:
    brand_options = sku[sku["category"].isin(category_sel)]["brand"].unique().tolist()
    brand_sel = st.multiselect("Brand", brand_options, default=brand_options)
with col3:
    campaign_type_sel = st.multiselect("Campaign Type", sku["campaign_type"].unique().tolist(), default=sku["campaign_type"].unique().tolist())

if len(date_range) == 2:
    d_start, d_end = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
    date_mask = (sku["start_date"] >= d_start) & (sku["start_date"] <= d_end)
else:
    d_start, d_end = sku["start_date"].min(), sku["start_date"].max()
    date_mask = pd.Series(True, index=sku.index)

fsku = sku[
    date_mask
    & sku["category"].isin(category_sel)
    & sku["brand"].isin(brand_sel)
    & sku["campaign_type"].isin(campaign_type_sel)
].copy()

if fsku.empty:
    st.warning("No SKU records match the current filters. Please adjust the date range or selections.")
    st.stop()

st.caption(
    f"Current scope: {len(fsku):,} campaign-SKU records from {d_start.date()} to {d_end.date()}."
)

sku_agg = fsku.groupby(["sku_id", "product_name", "brand", "category", "subcategory"]).agg(
    total_traffic=("traffic", "sum"),
    total_orders=("orders", "sum"),
    total_gmv=("gmv", "sum"),
    avg_ctr=("click_through_rate", "mean"),
    avg_refund=("refund_rate", "mean"),
    avg_sell_through=("sell_through_rate", "mean"),
    overpriced_flag=("overpriced_flag", "max"),
    weak_listing_flag=("weak_listing_flag", "max"),
    campaign_count=("campaign_id", "nunique"),
).reset_index()
sku_agg["conversion_rate"] = sku_agg["total_orders"] / sku_agg["total_traffic"]

traffic_median = sku_agg["total_traffic"].median()
cr_median = sku_agg["conversion_rate"].median()


def quadrant_code(row):
    high_traffic = row["total_traffic"] >= traffic_median
    high_cr = row["conversion_rate"] >= cr_median
    if high_traffic and not high_cr:
        return "drag"
    if high_traffic and high_cr:
        return "star"
    if not high_traffic and high_cr:
        return "potential"
    return "edge"


QUADRANT_LABELS = {
    "drag": "🔴 Drag SKUs: high traffic, low conversion",
    "star": "🟢 Star SKUs: high traffic, high conversion",
    "potential": "🔵 Potential SKUs: low traffic, high conversion",
    "edge": "⚪ Edge SKUs: low traffic, low conversion",
}

sku_agg["quadrant_code"] = sku_agg.apply(quadrant_code, axis=1)
sku_agg["quadrant"] = sku_agg["quadrant_code"].map(QUADRANT_LABELS)

n_drag = int((sku_agg["quadrant_code"] == "drag").sum())
drag_traffic_share = sku_agg.loc[sku_agg["quadrant_code"] == "drag", "total_traffic"].sum() / sku_agg["total_traffic"].sum()
n_star = int((sku_agg["quadrant_code"] == "star").sum())

c1, c2, c3, c4 = st.columns(4)
c1.metric("SKUs Analyzed", f"{len(sku_agg):,}")
c2.metric("🔴 Drag SKUs", f"{n_drag}", f"{drag_traffic_share * 100:.1f}% of traffic", delta_color="off")
c3.metric("🟢 Star SKUs", f"{n_star}")
c4.metric("Average Sell-through", fmt_pct(sku_agg["avg_sell_through"].mean()))

st.divider()

st.subheader("Traffic x Conversion Matrix")
fig = px.scatter(
    sku_agg,
    x="total_traffic",
    y="conversion_rate",
    color="quadrant",
    size="total_gmv",
    hover_data={
        "product_name": True,
        "brand": True,
        "total_gmv": ":.0f",
        "avg_refund": ":.2%",
        "campaign_count": True,
    },
    color_discrete_map={
        QUADRANT_LABELS["drag"]: "#ef4444",
        QUADRANT_LABELS["star"]: "#22c55e",
        QUADRANT_LABELS["potential"]: "#3b82f6",
        QUADRANT_LABELS["edge"]: "#9ca3af",
    },
    labels={"total_traffic": "Total Traffic", "conversion_rate": "Conversion Rate"},
    height=550,
)
fig.add_vline(x=traffic_median, line_dash="dash", line_color="gray", annotation_text="Traffic median")
fig.add_hline(y=cr_median, line_dash="dash", line_color="gray", annotation_text="Conversion median")
fig.update_yaxes(tickformat=".1%")
st.plotly_chart(fig, use_container_width=True)

with st.expander("📋 Quadrant interpretation"):
    quadrant_table = pd.DataFrame(
        [
            ["🟢 Star SKUs", "High traffic, high conversion", "Strong demand capture.", "Protect inventory and increase qualified exposure."],
            ["🔴 Drag SKUs", "High traffic, low conversion", "Exposure is being wasted.", "Fix listing content, pricing, inventory, and refund-risk signals first."],
            ["🔵 Potential SKUs", "Low traffic, high conversion", "Underexposed products.", "Test additional placement or campaign support."],
            ["⚪ Edge SKUs", "Low traffic, low conversion", "Weak traction.", "Deprioritize unless strategically important."],
        ],
        columns=["Segment", "Signal", "Meaning", "Recommended Action"],
    )
    st.dataframe(quadrant_table, use_container_width=True, hide_index=True)

st.subheader("🔴 Drag SKU Root-cause List")
drag_skus = sku_agg[sku_agg["quadrant_code"] == "drag"].copy().sort_values("total_traffic", ascending=False)


def diagnose(row):
    reasons = []
    if row["overpriced_flag"]:
        reasons.append("price competitiveness")
    if row["weak_listing_flag"]:
        reasons.append("listing content quality")
    if row["avg_ctr"] < fsku["click_through_rate"].median() * 0.8:
        reasons.append("low click-through rate")
    if row["avg_refund"] > fsku["refund_rate"].median() * 1.3:
        reasons.append("elevated refund risk")
    return ", ".join(reasons) if reasons else "requires merchandising review"


drag_skus["diagnosis"] = drag_skus.apply(diagnose, axis=1)
display_cols = drag_skus[
    [
        "product_name",
        "brand",
        "category",
        "total_traffic",
        "conversion_rate",
        "total_gmv",
        "avg_refund",
        "diagnosis",
    ]
].rename(
    columns={
        "product_name": "Product",
        "brand": "Brand",
        "category": "Category",
        "total_traffic": "Traffic",
        "conversion_rate": "Conversion Rate",
        "total_gmv": "GMV",
        "avg_refund": "Refund Rate",
        "diagnosis": "Likely Issue",
    }
)
display_cols["Conversion Rate"] = (display_cols["Conversion Rate"] * 100).round(2).astype(str) + "%"
display_cols["Refund Rate"] = (display_cols["Refund Rate"] * 100).round(2).astype(str) + "%"
display_cols["GMV"] = display_cols["GMV"].round(0)
st.dataframe(display_cols.head(30), use_container_width=True, hide_index=True)

st.download_button(
    "Download full drag SKU list (CSV)",
    drag_skus.to_csv(index=False, encoding="utf-8"),
    file_name="drag_sku_diagnosis.csv",
    mime="text/csv",
)

st.divider()
col_a, col_b = st.columns(2)
with col_a:
    st.subheader("Drag SKU Share by Brand")
    brand_quad = sku_agg.groupby(["brand", "quadrant_code"]).size().reset_index(name="count")
    brand_total = sku_agg.groupby("brand").size().reset_index(name="total")
    brand_quad = brand_quad.merge(brand_total, on="brand")
    brand_quad["pct"] = brand_quad["count"] / brand_quad["total"]
    drag_by_brand = brand_quad[brand_quad["quadrant_code"] == "drag"].sort_values("pct", ascending=False)
    fig4 = px.bar(
        drag_by_brand.head(12),
        x="pct",
        y="brand",
        orientation="h",
        labels={"pct": "Drag SKU Share", "brand": ""},
        color="pct",
        color_continuous_scale="Reds",
    )
    fig4.update_xaxes(tickformat=".0%")
    fig4.update_layout(height=420)
    st.plotly_chart(fig4, use_container_width=True)

with col_b:
    st.subheader("Sell-through vs Discount Rate")
    fdf2 = fsku.groupby(["sku_id", "product_name"]).agg(
        discount_rate=("discount_rate", "mean"),
        sell_through=("sell_through_rate", "mean"),
        stock=("stock_quantity", "mean"),
        gmv=("gmv", "sum"),
    ).reset_index()
    fig5 = px.scatter(
        fdf2,
        x="discount_rate",
        y="sell_through",
        size="stock",
        hover_data=["product_name"],
        labels={"discount_rate": "Discount Rate", "sell_through": "Sell-through Rate"},
        color="sell_through",
        color_continuous_scale="RdYlGn",
        height=420,
    )
    fig5.update_xaxes(tickformat=".0%")
    fig5.update_yaxes(tickformat=".0%")
    st.plotly_chart(fig5, use_container_width=True)
    st.caption("Large bubbles in the lower-left area indicate inventory risk: deep discounts with weak sell-through.")

with st.expander("📐 Drag SKU logic"):
    st.markdown(
        """
- A drag SKU has traffic above the selected-scope median and conversion below the selected-scope median.
- Diagnosis signals combine price flags, listing-quality flags, click-through rate, and refund rate.
- Brand-level drag share helps prioritize supplier or merchandising conversations.
"""
    )
