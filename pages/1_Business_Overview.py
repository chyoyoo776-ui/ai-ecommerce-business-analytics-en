# -*- coding: utf-8 -*-
"""Business Overview - operating health check."""

from pathlib import Path
import sys

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

sys.path.append(str(Path(__file__).parent.parent))
from utils import fmt_pct, fmt_revenue, load_daily_business, load_sku_performance, pct_delta


st.set_page_config(page_title="Business Overview", page_icon="📊", layout="wide")
st.title("📊 Business Overview")
st.caption("Operating health check across GMV, traffic, conversion, AOV, and channel performance.")

st.info(
    "This page decomposes GMV into traffic, conversion rate, order volume, and average order value. "
    "It compares the selected period with the previous equal-length period to flag material operating anomalies."
)

df = load_daily_business()

col_f1, col_f2 = st.columns([2, 1])
with col_f1:
    date_range = st.date_input(
        "Date range",
        value=(df["date"].max() - pd.Timedelta(days=90), df["date"].max()),
        min_value=df["date"].min(),
        max_value=df["date"].max(),
    )
with col_f2:
    channels_sel = st.multiselect(
        "Channels",
        options=df["channel"].unique().tolist(),
        default=df["channel"].unique().tolist(),
    )

if len(date_range) == 2:
    start, end = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
    mask = (df["date"] >= start) & (df["date"] <= end) & df["channel"].isin(channels_sel)
    fdf = df[mask].copy()
else:
    start, end = df["date"].min(), df["date"].max()
    fdf = df[df["channel"].isin(channels_sel)].copy()

if fdf.empty:
    st.warning("No data is available for the selected filters. Please adjust the date range or channels.")
    st.stop()

period_days = (fdf["date"].max() - fdf["date"].min()).days + 1
prev_start = fdf["date"].min() - pd.Timedelta(days=period_days)
prev_end = fdf["date"].min() - pd.Timedelta(days=1)
prev_df = df[
    (df["date"] >= prev_start)
    & (df["date"] <= prev_end)
    & df["channel"].isin(channels_sel)
]

st.caption(
    f"📅 Current period: {fdf['date'].min().date()} to {fdf['date'].max().date()} ({period_days} days). "
    f"Comparison period: {prev_start.date()} to {prev_end.date()}."
)

total_gmv = fdf["gmv"].sum()
total_traffic = fdf["traffic"].sum()
total_orders = fdf["orders"].sum()
avg_cr = total_orders / total_traffic if total_traffic else 0
avg_aov = total_gmv / total_orders if total_orders else 0
avg_refund = (fdf["refund_rate"] * fdf["gmv"]).sum() / total_gmv if total_gmv else 0

prev_gmv = prev_df["gmv"].sum()
prev_traffic = prev_df["traffic"].sum()
prev_orders = prev_df["orders"].sum()
prev_cr = prev_orders / prev_traffic if prev_traffic else 0
prev_aov = prev_gmv / prev_orders if prev_orders else 0

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("GMV", fmt_revenue(total_gmv), f"{pct_delta(total_gmv, prev_gmv) * 100:+.1f}%" if pct_delta(total_gmv, prev_gmv) is not None else None)
c2.metric("Traffic", f"{total_traffic:,.0f}", f"{pct_delta(total_traffic, prev_traffic) * 100:+.1f}%" if pct_delta(total_traffic, prev_traffic) is not None else None)
c3.metric("Conversion Rate", fmt_pct(avg_cr), f"{(avg_cr - prev_cr) * 100:+.2f}pp" if prev_traffic else None)
c4.metric("AOV", f"${avg_aov:,.0f}", f"{pct_delta(avg_aov, prev_aov) * 100:+.1f}%" if pct_delta(avg_aov, prev_aov) is not None else None)
c5.metric("Refund Rate", fmt_pct(avg_refund))

with st.expander("📐 KPI framework"):
    st.markdown("**GMV = Traffic x Conversion Rate x Average Order Value.** This decomposition drives the anomaly checks below.")

st.divider()

st.subheader("🩺 Operating Health Check")
st.caption("Flags material movement in GMV, traffic, conversion rate, AOV, and order volume.")

alerts = []
gmv_chg = pct_delta(total_gmv, prev_gmv)
traffic_chg = pct_delta(total_traffic, prev_traffic)
orders_chg = pct_delta(total_orders, prev_orders)
cr_chg = pct_delta(avg_cr, prev_cr)
aov_chg = pct_delta(avg_aov, prev_aov)

if gmv_chg is not None and gmv_chg < -0.15:
    alerts.append(("high", f"🔴 GMV declined {abs(gmv_chg) * 100:.1f}%", "GMV dropped materially versus the comparison period.", "Review traffic, conversion, and AOV to isolate the largest drag."))
if cr_chg is not None and cr_chg < -0.10:
    alerts.append(("medium", f"🟡 Conversion rate declined {abs(cr_chg) * 100:.1f}%", "Conversion efficiency weakened.", "Use Product Diagnosis to inspect high-traffic, low-conversion SKUs."))
if aov_chg is not None and aov_chg < -0.10:
    alerts.append(("medium", f"🟡 AOV declined {abs(aov_chg) * 100:.1f}%", "Average order value fell materially.", "Review discount depth, bundle strategy, and premium product mix."))
if orders_chg is not None and orders_chg < -0.15:
    alerts.append(("high", f"🔴 Orders declined {abs(orders_chg) * 100:.1f}%", "Order volume weakened materially.", "Review campaign calendar and channel allocation."))

traffic_mismatch = False
if traffic_chg is not None and traffic_chg > 0.20 and (orders_chg is None or orders_chg < 0.05):
    traffic_mismatch = True
    alerts.append(("medium", "🟡 Traffic and conversion mismatch", "Traffic increased, but order volume did not keep pace.", "Review traffic quality, landing page fit, pricing, and inventory availability."))

sku_all = load_sku_performance()
sku_in_range = sku_all[(sku_all["start_date"] >= start) & (sku_all["start_date"] <= end)]
n_problem_sku = 0
drag_traffic_share = 0
if len(sku_in_range) > 10:
    s_agg = sku_in_range.groupby("sku_id").agg(
        traffic=("traffic", "sum"),
        orders=("orders", "sum"),
    ).reset_index()
    s_agg["conversion_rate"] = s_agg["orders"] / s_agg["traffic"]
    traffic_t = s_agg["traffic"].quantile(0.7)
    cr_t = s_agg["conversion_rate"].quantile(0.3)
    problem_mask = (s_agg["traffic"] >= traffic_t) & (s_agg["conversion_rate"] <= cr_t)
    n_problem_sku = int(problem_mask.sum())
    drag_traffic_share = s_agg.loc[problem_mask, "traffic"].sum() / s_agg["traffic"].sum() if s_agg["traffic"].sum() else 0
    if n_problem_sku:
        alerts.append(("high", f"🔴 {n_problem_sku} high-traffic, low-conversion SKUs found", f"These SKUs account for {drag_traffic_share * 100:.1f}% of selected SKU traffic.", "Prioritize product content, pricing, inventory, and refund-risk review."))

score = 100
for severity, *_ in alerts:
    score -= 20 if severity == "high" else 10
score = max(score, 0)
score_label = "🟢 Healthy" if score >= 80 else ("🟡 Needs Attention" if score >= 50 else "🔴 Immediate Action Needed")

sh1, sh2 = st.columns([1, 3])
with sh1:
    st.metric("Health Score", f"{score} / 100", score_label, delta_color="off")
with sh2:
    if alerts:
        high = sum(1 for a in alerts if a[0] == "high")
        medium = sum(1 for a in alerts if a[0] == "medium")
        st.warning(f"{high} high-priority and {medium} medium-priority issues were detected for the selected scope.")
    else:
        st.success("No material anomaly was detected for the selected scope.")

for _, title, message, action in alerts:
    with st.container(border=True):
        st.markdown(f"**{title}**")
        st.caption(f"📌 Signal: {message}")
        st.caption(f"👉 Recommended next step: {action}")

if n_problem_sku > 0:
    st.page_link("pages/2_Product_Diagnosis.py", label="👉 Open Product Diagnosis")

st.markdown("#### 🧩 Root Cause Summary")
causes = []
actions = set()
if gmv_chg is not None and gmv_chg < -0.05:
    if orders_chg is not None and orders_chg < -0.10:
        causes.append("order-volume decline")
        actions.add("campaign cadence and resource allocation")
    if cr_chg is not None and cr_chg < -0.08:
        causes.append("conversion weakness")
        actions.add("high-traffic SKU content, pricing, and inventory")
    if aov_chg is not None and aov_chg < -0.08:
        causes.append("AOV compression")
        actions.add("discount depth and product mix")
    if traffic_mismatch:
        causes.append("unconverted incremental traffic")
        actions.add("channel traffic quality and landing-page fit")
    if n_problem_sku > 5:
        causes.append(f"{n_problem_sku} traffic-wasting SKUs")
        actions.add("the product diagnosis list")

    if causes:
        st.error(f"GMV pressure appears to be driven by **{', '.join(causes)}**. Prioritize **{', '.join(actions)}**.")
    else:
        st.warning("GMV declined, but the component movements did not exceed alert thresholds. Drill into brand and channel slices for more context.")
elif gmv_chg is not None and gmv_chg > 0.05:
    st.success(f"GMV increased {gmv_chg * 100:.1f}% versus the comparison period. Current operating momentum looks healthy.")
else:
    st.info("GMV is broadly stable versus the comparison period.")

st.divider()

daily_agg = fdf.groupby("date").agg(
    gmv=("gmv", "sum"),
    traffic=("traffic", "sum"),
    orders=("orders", "sum"),
    is_promotion_day=("is_promotion_day", "max"),
    promotion_name=("promotion_name", "max"),
).reset_index()
daily_agg["conversion_rate"] = daily_agg["orders"] / daily_agg["traffic"]

fig = go.Figure()
fig.add_trace(
    go.Bar(
        x=daily_agg["date"],
        y=daily_agg["gmv"] / 1000,
        name="GMV ($K)",
        marker_color=daily_agg["is_promotion_day"].map({True: "#f59e0b", False: "#93c5fd"}),
    )
)
fig.add_trace(
    go.Scatter(
        x=daily_agg["date"],
        y=daily_agg["conversion_rate"] * 100,
        name="Conversion Rate (%)",
        yaxis="y2",
        line=dict(color="#059669", width=2),
    )
)
fig.update_layout(
    title="Daily GMV and Conversion Rate",
    yaxis=dict(title="GMV ($K)"),
    yaxis2=dict(title="Conversion Rate (%)", overlaying="y", side="right"),
    legend=dict(orientation="h", yanchor="bottom", y=1.02),
    height=420,
    hovermode="x unified",
)
st.plotly_chart(fig, use_container_width=True)

col_a, col_b = st.columns(2)
with col_a:
    monthly = df[df["channel"].isin(channels_sel)].copy()
    monthly["month"] = monthly["date"].dt.to_period("M").astype(str)
    monthly_agg = monthly.groupby("month").agg(gmv=("gmv", "sum")).reset_index()
    fig2 = px.bar(monthly_agg, x="month", y="gmv", title="Monthly GMV", color_discrete_sequence=["#2563eb"])
    fig2.update_layout(height=360)
    st.plotly_chart(fig2, use_container_width=True)

with col_b:
    ch_agg = fdf.groupby("channel").agg(gmv=("gmv", "sum"), traffic=("traffic", "sum"), orders=("orders", "sum")).reset_index()
    ch_agg["conversion_rate"] = ch_agg["orders"] / ch_agg["traffic"]
    fig3 = px.bar(
        ch_agg.sort_values("gmv"),
        x="gmv",
        y="channel",
        orientation="h",
        title="GMV Contribution by Channel",
        color="conversion_rate",
        color_continuous_scale="Blues",
        labels={"gmv": "GMV", "channel": ""},
    )
    fig3.update_layout(height=360)
    st.plotly_chart(fig3, use_container_width=True)

st.subheader("Channel Performance")
ch_table = fdf.groupby("channel").agg(
    Traffic=("traffic", "sum"),
    Orders=("orders", "sum"),
    GMV=("gmv", "sum"),
    Refund_Rate=("refund_rate", "mean"),
).reset_index()
ch_table["Conversion Rate"] = (ch_table["Orders"] / ch_table["Traffic"] * 100).round(2).astype(str) + "%"
ch_table["AOV"] = (ch_table["GMV"] / ch_table["Orders"]).round(1)
ch_table["GMV"] = ch_table["GMV"].round(0)
ch_table["Refund Rate"] = (ch_table["Refund_Rate"] * 100).round(2).astype(str) + "%"
ch_table = ch_table.rename(columns={"channel": "Channel"})
st.dataframe(
    ch_table[["Channel", "Traffic", "Orders", "GMV", "Conversion Rate", "AOV", "Refund Rate"]],
    use_container_width=True,
    hide_index=True,
)

with st.expander("📎 How to read channel metrics"):
    st.markdown(
        """
- Private-community and CRM-driven channels should usually convert above the platform average because the audience has stronger intent.
- Promotion days can create GMV spikes while compressing AOV because price-sensitive demand increases.
- Channels with high traffic share and weak conversion deserve landing-page, audience-fit, and product-match review.
"""
    )
