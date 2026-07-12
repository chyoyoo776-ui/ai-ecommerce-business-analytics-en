# -*- coding: utf-8 -*-
"""Business Overview (EN) — Platform performance overview, English version"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from utils import load_daily_business, load_sku_performance, fmt_pct, pct_delta

st.set_page_config(page_title="Business Overview", page_icon="📊", layout="wide")
st.title("📊 Business Overview")
st.caption("Core KPI monitoring · Multi-channel traffic breakdown")

# Channel names in the underlying data are stored in Chinese; map them to English for display only.
CHANNEL_EN = {
    "线下门店导流": "Offline Store Referral",
    "短信营销": "SMS Marketing",
    "微信推文": "WeChat Article",
    "私域社群": "Private Community",
    "App自然流量": "App Organic Traffic",
}
CHANNEL_ZH = {v: k for k, v in CHANNEL_EN.items()}

st.info(
    "**This page answers**: Is current business performance healthy? Is the issue coming from GMV, "
    "traffic, conversion rate, or AOV?\n\n"
    "This page runs a business health check under the selected time/channel filters, decomposing GMV "
    "into traffic, conversion rate, order volume, and AOV, comparing against the prior period to flag "
    "abnormal swings, and ending with a one-line synthesized diagnosis."
)

df = load_daily_business()

# ---- Filters ----
col_f1, col_f2 = st.columns([2, 1])
with col_f1:
    date_range = st.date_input(
        "Select date range",
        value=(df["date"].max() - pd.Timedelta(days=90), df["date"].max()),
        min_value=df["date"].min(),
        max_value=df["date"].max(),
    )
with col_f2:
    channel_options_en = [CHANNEL_EN[c] for c in df["channel"].unique().tolist()]
    channels_sel_en = st.multiselect("Filter channel", options=channel_options_en, default=channel_options_en)
    channels_sel = [CHANNEL_ZH[c] for c in channels_sel_en]

if len(date_range) == 2:
    start, end = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
    mask = (df["date"] >= start) & (df["date"] <= end) & (df["channel"].isin(channels_sel))
    fdf = df[mask].copy()
else:
    start, end = df["date"].min(), df["date"].max()
    fdf = df[df["channel"].isin(channels_sel)].copy()

# Period-over-period comparison against the immediately preceding equal-length window (NOT year-over-year)
period_days = (fdf["date"].max() - fdf["date"].min()).days + 1
prev_start = fdf["date"].min() - pd.Timedelta(days=period_days)
prev_end = fdf["date"].min() - pd.Timedelta(days=1)
prev_df = df[(df["date"] >= prev_start) & (df["date"] <= prev_end) & (df["channel"].isin(channels_sel))]

st.caption(
    f"📅 Current period: {fdf['date'].min().date()} ~ {fdf['date'].max().date()} ({period_days} days)　"
    f"Compared to (prior equal-length period, NOT year-over-year): {prev_start.date()} ~ {prev_end.date()}"
)

# ---- KPI cards ----
total_gmv = fdf["gmv"].sum()
total_uv = fdf["traffic"].sum()
total_orders = fdf["orders"].sum()
avg_cr = total_orders / total_uv if total_uv else 0
avg_aov = total_gmv / total_orders if total_orders else 0
avg_refund = (fdf["refund_rate"] * fdf["gmv"]).sum() / total_gmv if total_gmv else 0

prev_gmv = prev_df["gmv"].sum()
prev_uv = prev_df["traffic"].sum()
prev_orders = prev_df["orders"].sum()
prev_cr = prev_orders / prev_uv if prev_uv else 0
prev_aov = prev_gmv / prev_orders if prev_orders else 0

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("GMV", f"¥{total_gmv/10000:,.1f}K", f"{pct_delta(total_gmv, prev_gmv)*100:+.1f}%" if pct_delta(total_gmv, prev_gmv) is not None else None,
          help="Compared to the prior equal-length period (period-over-period, not YoY)")
c2.metric("UV", f"{total_uv:,.0f}", f"{pct_delta(total_uv, prev_uv)*100:+.1f}%" if pct_delta(total_uv, prev_uv) is not None else None,
          help="Compared to the prior equal-length period (period-over-period, not YoY)")
c3.metric("Conversion Rate", fmt_pct(avg_cr), f"{(avg_cr-prev_cr)*100:+.2f}pp" if prev_uv else None,
          help="pp = percentage points, vs. the prior equal-length period")
c4.metric("AOV", f"¥{avg_aov:,.0f}", f"{pct_delta(avg_aov, prev_aov)*100:+.1f}%" if pct_delta(avg_aov, prev_aov) is not None else None,
          help="Compared to the prior equal-length period (period-over-period, not YoY)")
c5.metric("Refund Rate", fmt_pct(avg_refund), help="GMV-weighted average refund rate in the current period")

with st.expander("📐 Metric decomposition logic"):
    st.markdown("GMV = UV × Conversion Rate × AOV　——　this is the base formula behind every anomaly check on this page. A meaningful swing in any single factor propagates down into GMV.")

st.divider()

# ============================================================
# Business Health Check
# ============================================================
st.subheader("🩺 Business Health Check")
st.caption("Under the current filters, checks GMV / traffic / conversion rate / AOV / order volume for period-over-period swings, and flags traffic-conversion mismatch and high-traffic low-conversion SKU issues.")

alerts = []  # (severity, title, message, next_action)

gmv_chg = pct_delta(total_gmv, prev_gmv)
cr_chg = pct_delta(avg_cr, prev_cr)
aov_chg = pct_delta(avg_aov, prev_aov)
orders_chg = pct_delta(total_orders, prev_orders)
uv_chg = pct_delta(total_uv, prev_uv)

# --- Tier 1: KPI period-over-period fluctuation check ---
if gmv_chg is not None and gmv_chg < -0.15:
    alerts.append(("high", f"🔴 GMV declined {abs(gmv_chg)*100:.1f}% period-over-period",
                    "GMV dropped notably vs. the prior period.",
                    "Check traffic, conversion rate, and AOV to isolate the primary drag factor."))
if cr_chg is not None and cr_chg < -0.10:
    alerts.append(("medium", f"🟡 Conversion rate declined {abs(cr_chg)*100:.1f}% period-over-period",
                    "Conversion efficiency dropped — possibly related to product content, pricing, stock, or traffic quality.",
                    "Go to the Product Diagnosis page to check high-traffic low-conversion SKUs, listing content, and price competitiveness."))
if aov_chg is not None and aov_chg < -0.10:
    alerts.append(("medium", f"🟡 AOV declined {abs(aov_chg)*100:.1f}% period-over-period",
                    "AOV dropped notably — check discount depth or a shift away from higher-priced items.",
                    "Review recent campaign discount depth and evaluate whether the discount structure needs adjustment."))
if orders_chg is not None and orders_chg < -0.15:
    alerts.append(("high", f"🔴 Order volume declined {abs(orders_chg)*100:.1f}% period-over-period",
                    "Order volume dropped notably — check for reduced campaign resources or a traffic decline.",
                    "Verify whether this period had fewer scheduled campaigns than the prior period, and assess whether more campaign slots are needed."))

# --- Tier 2: Traffic-conversion mismatch check ---
traffic_mismatch = False
if uv_chg is not None and uv_chg > 0.20 and (orders_chg is None or orders_chg < 0.05):
    traffic_mismatch = True
    alerts.append(("medium", "🟡 Traffic-Conversion Mismatch",
                    f"Traffic grew {uv_chg*100:.1f}% period-over-period, but orders only grew "
                    f"{(orders_chg*100 if orders_chg is not None else 0):.1f}%, meaning new traffic isn't converting well.",
                    "Check traffic source quality, pricing, page appeal, and stock levels."))

# --- Tier 3: SKU-level issue detection (linked to Product Diagnosis page) ---
# Uses the same median-split method as the Product Diagnosis page (standard four-quadrant approach):
# "traffic ≥ median AND conversion rate < median" — this keeps both pages consistent for the same window.
sku_all = load_sku_performance()
sku_in_range = sku_all[(sku_all["start_date"] >= start) & (sku_all["start_date"] <= end)]
n_problem_sku = 0
drag_uv_share_range = 0
if len(sku_in_range) > 10:
    s_agg = sku_in_range.groupby("sku_id").agg(uv=("traffic", "sum"), orders=("orders", "sum")).reset_index()
    s_agg["cr"] = s_agg["orders"] / s_agg["uv"]
    uv_t = s_agg["uv"].median()
    cr_t = s_agg["cr"].median()
    problem_mask = (s_agg["uv"] >= uv_t) & (s_agg["cr"] < cr_t)
    n_problem_sku = problem_mask.sum()
    drag_uv_share_range = s_agg.loc[problem_mask, "uv"].sum() / s_agg["uv"].sum() if s_agg["uv"].sum() else 0
    if n_problem_sku > 0:
        alerts.append(("high", f"🔴 Found {n_problem_sku} high-traffic low-conversion SKUs",
                        f"These SKUs received high exposure (accounting for {drag_uv_share_range*100:.1f}% of total traffic in the current range), but convert below the current range's median.",
                        "Go to Product Diagnosis for the full list — prioritize checking titles, main images, pricing, and stock status."))

# --- Health score ---
score = 100
for sev, _, _, _ in alerts:
    score -= 20 if sev == "high" else (10 if sev == "medium" else 5)
score = max(score, 0)
score_label = "🟢 Healthy" if score >= 80 else ("🟡 Needs Attention" if score >= 50 else "🔴 Needs Immediate Action")

sh1, sh2 = st.columns([1, 3])
with sh1:
    st.metric("Business Health Score", f"{score} / 100", score_label, delta_color="off")
with sh2:
    if alerts:
        n_high = sum(1 for a in alerts if a[0] == "high")
        n_med = sum(1 for a in alerts if a[0] == "medium")
        st.warning(f"Found {n_high} high-priority and {n_med} medium-priority issues under current filters — see diagnostic cards below.")
    else:
        st.success("No significant issues detected under current filters — core metrics are stable.")

for sev, title, msg, action in alerts:
    with st.container(border=True):
        st.markdown(f"**{title}**")
        st.caption(f"📌 Observation: {msg}")
        st.caption(f"👉 Suggested next step: {action}")

if n_problem_sku > 0:
    st.page_link("pages/2_Product_Diagnosis.py", label="👉 Go to Product Diagnosis for the full drag-SKU list")

# ---- Tier 3: Synthesized diagnostic conclusion (templated output) ----
st.markdown("#### 🧩 Synthesized Diagnosis")
causes = []
actions = set()

if gmv_chg is not None and gmv_chg < -0.05:
    if orders_chg is not None and orders_chg < -0.10:
        causes.append("declining order volume")
        actions.add("campaign resource pacing and landing pages")
    if cr_chg is not None and cr_chg < -0.08:
        causes.append("insufficient conversion follow-through")
        actions.add("titles, main images, pricing, and stock status of high-traffic low-conversion SKUs")
    if aov_chg is not None and aov_chg < -0.08:
        causes.append("declining AOV")
        actions.add("discount depth and product mix")
    if traffic_mismatch:
        causes.append("new traffic not converting effectively")
        actions.add("traffic source quality and landing page experience")
    if n_problem_sku > 5:
        causes.append(f"{n_problem_sku} high-traffic low-conversion SKUs dragging performance")
        actions.add("the drag-SKU list on the Product Diagnosis page")

    if causes:
        cause_text = ", ".join(causes)
        action_text = ", ".join(actions)
        st.error(f"**Synthesized diagnosis**: The current GMV decline is mainly related to **{cause_text}**. Prioritize investigating **{action_text}**.")
    else:
        st.warning("**Synthesized diagnosis**: GMV declined, but none of the individual metric swings exceeded the alert threshold — consider drilling down by specific brand/channel.")
elif gmv_chg is not None and gmv_chg > 0.05:
    st.success(f"**Synthesized diagnosis**: GMV grew {gmv_chg*100:.1f}% vs. the prior period — core metrics look healthy. Consider maintaining the current campaign resource pace.")
else:
    st.info("**Synthesized diagnosis**: GMV is roughly stable, with period-over-period swings within a normal range — no major business issue requires attention right now.")

st.divider()

# ---- Daily GMV trend chart (dual axis: GMV bars + conversion rate line) ----
daily_agg = fdf.groupby("date").agg(
    gmv=("gmv", "sum"), uv=("traffic", "sum"), orders=("orders", "sum"),
    is_festival=("is_promotion_day", "max"), festival_name=("promotion_name", "max")
).reset_index()
daily_agg["conversion_rate"] = daily_agg["orders"] / daily_agg["uv"]

fig = go.Figure()
fig.add_trace(go.Bar(
    x=daily_agg["date"], y=daily_agg["gmv"]/10000, name="GMV(¥0K)",
    marker_color=daily_agg["is_festival"].map({True: "#f59e0b", False: "#93c5fd"}),
))
fig.add_trace(go.Scatter(
    x=daily_agg["date"], y=daily_agg["conversion_rate"]*100, name="Conversion Rate(%)",
    yaxis="y2", line=dict(color="#059669", width=2),
))
fig.update_layout(
    title="Daily GMV Trend (orange = promo day) & Conversion Rate",
    yaxis=dict(title="GMV(¥0K)"),
    yaxis2=dict(title="Conversion Rate(%)", overlaying="y", side="right"),
    legend=dict(orientation="h", yanchor="bottom", y=1.02),
    height=420, hovermode="x unified",
)
st.plotly_chart(fig, use_container_width=True)

# ---- Monthly trend + channel breakdown ----
col_a, col_b = st.columns(2)

with col_a:
    monthly = df[df["channel"].isin(channels_sel)].copy()
    monthly["month"] = monthly["date"].dt.to_period("M").astype(str)
    monthly_agg = monthly.groupby("month").agg(gmv=("gmv", "sum")).reset_index()
    monthly_agg["mom"] = monthly_agg["gmv"].pct_change()
    fig2 = px.bar(monthly_agg, x="month", y="gmv", title="Monthly GMV Trend(¥)",
                  color_discrete_sequence=["#2563eb"])
    fig2.update_layout(height=360)
    st.plotly_chart(fig2, use_container_width=True)

with col_b:
    ch_agg = fdf.groupby("channel").agg(gmv=("gmv", "sum"), uv=("traffic", "sum")).reset_index()
    ch_agg["conversion_rate"] = fdf.groupby("channel").apply(
        lambda x: x["orders"].sum() / x["uv"].sum(), include_groups=False
    ).values
    ch_agg["channel"] = ch_agg["channel"].map(CHANNEL_EN)
    fig3 = px.bar(ch_agg.sort_values("gmv"), x="gmv", y="channel", orientation="h",
                  title="GMV Contribution by Channel", color="conversion_rate",
                  color_continuous_scale="Blues", labels={"gmv": "GMV(¥)", "channel": ""})
    fig3.update_layout(height=360)
    st.plotly_chart(fig3, use_container_width=True)

# ---- Channel efficiency comparison table ----
st.subheader("Channel Efficiency Comparison")
ch_table = fdf.groupby("channel").agg(
    UV=("traffic", "sum"), Orders=("orders", "sum"), GMV=("gmv", "sum"), RefundRate=("refund_rate", "mean")
).reset_index()
ch_table["CVR"] = (ch_table["Orders"] / ch_table["UV"] * 100).round(2).astype(str) + "%"
ch_table["AOV"] = (ch_table["GMV"] / ch_table["Orders"]).round(1)
ch_table["GMV"] = ch_table["GMV"].round(0)
ch_table["RefundRate"] = (ch_table["RefundRate"] * 100).round(2).astype(str) + "%"
ch_table["channel"] = ch_table["channel"].map(CHANNEL_EN)
ch_table = ch_table.rename(columns={"channel": "Channel", "RefundRate": "Refund Rate"})
st.dataframe(
    ch_table[["Channel", "UV", "Orders", "GMV", "CVR", "AOV", "Refund Rate"]],
    use_container_width=True, hide_index=True
)

with st.expander("📎 How to read channel metrics"):
    st.markdown("""
    - **Private Community** channel conversion is typically well above the overall average, suggesting
      higher trust and purchase intent among these users — a priority channel for more content investment
      and exclusive coupons.
    - **Promo days** (orange bars) show pulse-like GMV growth, but AOV usually dips slightly, indicating a
      higher share of price-sensitive buyers during promotions.
    - If a channel has a high traffic share but noticeably low conversion, investigate whether its landing
      pages match the target audience.
    """)
