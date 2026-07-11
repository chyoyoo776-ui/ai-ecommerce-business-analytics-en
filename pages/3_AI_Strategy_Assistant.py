# -*- coding: utf-8 -*-
"""AI Strategy Assistant - structured recommendations and impact sizing."""

from pathlib import Path
import sys

import pandas as pd
import streamlit as st

sys.path.append(str(Path(__file__).parent.parent))
from utils import load_brand_campaigns, load_daily_business, load_sku_performance


st.set_page_config(page_title="AI Strategy Assistant", page_icon="🤖", layout="wide")
st.title("🤖 AI Strategy Assistant")
st.caption("Turn operating signals into strategic recommendations, expected impact, and follow-up tracking.")

st.info(
    "This page combines business health and product diagnosis outputs into a structured strategy workflow: "
    "identify the issue, diagnose likely causes, recommend action, estimate business impact, and define validation metrics."
)

try:
    shared_key = st.secrets["ANTHROPIC_API_KEY"]
except Exception:
    shared_key = None

if shared_key:
    api_key = shared_key
    st.success("✅ A configured Anthropic API key is available for this app session.", icon="🔑")
else:
    st.info("💡 Enter an Anthropic API key to generate AI recommendations. The key is used only for this session and is not written to the repository.", icon="🔑")
    api_key = st.text_input("Anthropic API Key", type="password", placeholder="sk-ant-...")

sku = load_sku_performance()
campaigns = load_brand_campaigns()
daily = load_daily_business()

st.subheader("📝 Generate Strategic Recommendation Report")
st.caption("The report follows a fixed analytics structure: business issue, root-cause hypothesis, priority actions, expected impact, tracking metrics, and validation experiment.")

max_date = sku["end_date"].max()
col1, col2, col3 = st.columns(3)
with col1:
    report_scope = st.selectbox("Analysis scope", ["Platform", "Brand", "Category"])
with col2:
    scope_value = None
    if report_scope == "Brand":
        scope_value = st.selectbox("Brand", sorted(sku["brand"].unique().tolist()))
    elif report_scope == "Category":
        scope_value = st.selectbox("Category", sorted(sku["category"].unique().tolist()))
with col3:
    window_option = st.selectbox("Time window", ["Last 7 days", "Last 30 days", "Last 90 days", "All data"], index=1)

window_days_map = {"Last 7 days": 7, "Last 30 days": 30, "Last 90 days": 90, "All data": None}
window_days = window_days_map[window_option]
if window_days is not None:
    window_start = max_date - pd.Timedelta(days=window_days)
    st.caption(f"📅 Analysis period: {window_start.date()} to {max_date.date()} ({window_days} days from the latest data date).")
else:
    window_start = sku["start_date"].min()
    st.caption(f"📅 Analysis period: {window_start.date()} to {max_date.date()} (all available data).")

generate_btn = st.button("📝 Generate strategy report", type="primary", use_container_width=True)


def build_data_context(scope, value, window_start=None, window_end=None):
    if scope == "Brand":
        s = sku[sku["brand"] == value]
        c = campaigns[campaigns["brand"] == value]
    elif scope == "Category":
        s = sku[sku["category"] == value]
        c = campaigns[campaigns["category"] == value]
    else:
        s = sku
        c = campaigns

    if window_start is not None:
        s = s[(s["start_date"] >= window_start) & (s["start_date"] <= window_end)]
        c = c[(c["start_date"] >= window_start) & (c["start_date"] <= window_end)]

    if s.empty:
        return None

    agg = s.groupby(["sku_id", "product_name", "brand"]).agg(
        traffic=("traffic", "sum"),
        orders=("orders", "sum"),
        gmv=("gmv", "sum"),
        refund_rate=("refund_rate", "mean"),
        sell_through=("sell_through_rate", "mean"),
        overpriced=("overpriced_flag", "max"),
        weak_listing=("weak_listing_flag", "max"),
    ).reset_index()
    agg["conversion_rate"] = agg["orders"] / agg["traffic"]
    traffic_med = agg["traffic"].median()
    cr_med = agg["conversion_rate"].median()

    drag = agg[(agg["traffic"] >= traffic_med) & (agg["conversion_rate"] < cr_med)].sort_values("traffic", ascending=False).head(10)
    stars = agg[(agg["traffic"] >= traffic_med) & (agg["conversion_rate"] >= cr_med)].sort_values("gmv", ascending=False).head(5)
    low_sell_through = agg[agg["sell_through"] < agg["sell_through"].quantile(0.2)].sort_values("gmv", ascending=False).head(10)
    recent_campaigns = c.sort_values("start_date", ascending=False).head(8)

    return f"""
Analysis scope: {scope}: {value or 'Platform'}
Analysis period: {window_start.date() if window_start is not None else s['start_date'].min().date()} to {window_end.date() if window_end is not None else s['start_date'].max().date()}

Overall scale:
- SKU count: {len(agg)}
- Total GMV: ${agg['gmv'].sum():,.0f}
- Average conversion rate: {agg['conversion_rate'].mean() * 100:.2f}%
- Average sell-through rate: {agg['sell_through'].mean() * 100:.1f}%
- Average refund rate: {agg['refund_rate'].mean() * 100:.2f}%

Top drag SKUs: high traffic, low conversion
{drag[['product_name', 'brand', 'traffic', 'conversion_rate', 'gmv', 'overpriced', 'weak_listing']].to_string(index=False)}

Top star SKUs: high traffic, high conversion
{stars[['product_name', 'brand', 'traffic', 'conversion_rate', 'gmv']].to_string(index=False)}

Low sell-through risk list
{low_sell_through[['product_name', 'brand', 'sell_through', 'gmv']].to_string(index=False)}

Recent campaign performance
{recent_campaigns[['brand', 'campaign_type', 'gmv', 'conversion_rate', 'new_customer_ratio']].to_string(index=False)}
"""


SYSTEM_PROMPT = """You are a senior e-commerce business analytics strategy assistant.
You receive structured operating data and produce a concise, action-oriented strategy report.

Return the report in English using exactly these six Markdown sections:

## 1. Key Business Issue
Summarize the most important business issue in 1-2 sentences and cite specific numbers.

## 2. Root Cause Hypothesis
Explain likely causes such as product content, price competitiveness, inventory, traffic quality, discounting, or refund risk. Ground the explanation in the data.

## 3. Priority Actions
List 3-5 concrete actions in priority order. Each action should reference specific brands, products, metrics, or segments when available.

## 4. Expected Business Impact
Describe the expected business impact, including conversion-rate improvement, GMV upside, AOV protection, or risk reduction.

## 5. Metrics to Track
List 3-5 follow-up metrics and the recommended monitoring cadence.

## 6. Suggested A/B Test
Provide one practical A/B test with hypothesis, control, treatment, primary metric, secondary metrics, guardrail metrics, and observation window.

Use crisp professional business language. Do not add greetings or generic disclaimers.
"""

if generate_btn:
    if not api_key:
        st.error("Please enter an Anthropic API key before generating a report.")
    else:
        with st.spinner("Analyzing the selected data and generating recommendations..."):
            try:
                from anthropic import Anthropic

                client = Anthropic(api_key=api_key)
                data_context = build_data_context(report_scope, scope_value, window_start, max_date)
                if data_context is None:
                    st.warning("No data is available for the selected scope and time window.")
                    st.stop()

                message = client.messages.create(
                    model="claude-sonnet-4-5",
                    max_tokens=2200,
                    system=SYSTEM_PROMPT,
                    messages=[{"role": "user", "content": f"Generate a structured strategy report using this data:\n{data_context}"}],
                )
                report_text = message.content[0].text
                st.session_state["last_report"] = report_text
                st.session_state["last_context"] = data_context
            except Exception as exc:
                st.error(f"Report generation failed: {exc}")

if "last_report" in st.session_state:
    st.divider()
    st.markdown(st.session_state["last_report"])
    st.download_button(
        "Download report (Markdown)",
        st.session_state["last_report"],
        file_name="strategy_recommendation_report.md",
        mime="text/markdown",
    )
    with st.expander("View data context sent to the assistant"):
        st.text(st.session_state["last_context"])
else:
    with st.expander("📄 Preview report structure"):
        st.markdown(
            """
## 1. Key Business Issue
The selected period contains 18 high-traffic, low-conversion SKUs representing 27.3% of SKU traffic, making product conversion the primary operating issue.

## 2. Root Cause Hypothesis
The drag SKU set is concentrated in products with price-competitiveness and listing-quality flags, suggesting weak demand capture rather than insufficient exposure.

## 3. Priority Actions
1. Refresh content and offer design for the top traffic-wasting SKUs.
2. Review price positioning for SKUs flagged as overpriced.
3. Shift incremental exposure toward high-conversion potential SKUs.

## 4. Expected Business Impact
Improving the top drag SKUs by 0.5 percentage points in conversion rate can create measurable GMV upside, which can be estimated in the calculator below.

## 5. Metrics to Track
CTR, conversion rate, GMV, refund rate, and sell-through rate should be reviewed weekly.

## 6. Suggested A/B Test
Test upgraded product content and offer messaging against the current listing. Use conversion rate as the primary metric and refund rate as a guardrail.
"""
        )

st.divider()

st.subheader("🧮 GMV Impact Calculator")
st.markdown(
    """
Estimate the GMV upside from improving high-traffic, low-conversion SKUs.

**Potential GMV uplift = Traffic x conversion-rate lift x average order value**
"""
)
st.warning("⚠️ This is a planning estimate, not a predictive model. Use it to size opportunities and prioritize tests.")

sku_agg_calc = sku.groupby(["sku_id", "product_name", "brand", "category"]).agg(
    total_traffic=("traffic", "sum"),
    total_orders=("orders", "sum"),
    total_gmv=("gmv", "sum"),
).reset_index()
sku_agg_calc["conversion_rate"] = sku_agg_calc["total_orders"] / sku_agg_calc["total_traffic"]
traffic_med_c = sku_agg_calc["total_traffic"].median()
cr_med_c = sku_agg_calc["conversion_rate"].median()
drag_calc = sku_agg_calc[
    (sku_agg_calc["total_traffic"] >= traffic_med_c)
    & (sku_agg_calc["conversion_rate"] < cr_med_c)
].copy()
drag_calc["aov"] = drag_calc["total_gmv"] / drag_calc["total_orders"].replace(0, pd.NA)
drag_calc = drag_calc.dropna(subset=["aov"]).sort_values("total_traffic", ascending=False)

calc_mode = st.radio("Calculation scope", ["Single drag SKU", "All drag SKUs"], horizontal=True)
cc1, cc2 = st.columns(2)

if calc_mode == "Single drag SKU":
    with cc1:
        sku_label_map = {f"{row.product_name} ({row.brand})": row.sku_id for row in drag_calc.itertuples()}
        picked_label = st.selectbox("Drag SKU", list(sku_label_map.keys()))
        picked = drag_calc[drag_calc["sku_id"] == sku_label_map[picked_label]].iloc[0]
        traffic = st.number_input("Traffic", value=int(picked["total_traffic"]), min_value=0)
        aov_input = st.number_input("AOV ($)", value=round(float(picked["aov"]), 1), min_value=0.0)
    with cc2:
        current_cr = st.number_input("Current conversion rate (%)", value=round(float(picked["conversion_rate"]) * 100, 2), min_value=0.0, max_value=100.0)
        cr_lift = st.number_input("Target lift (percentage points)", value=0.5, min_value=0.0, max_value=50.0, step=0.1)

    uplift_orders = traffic * (cr_lift / 100)
    uplift_gmv = traffic * (cr_lift / 100) * aov_input

    st.divider()
    r1, r2, r3 = st.columns(3)
    r1.metric("Current Conversion", f"{current_cr:.2f}%")
    r2.metric("Target Conversion", f"{current_cr + cr_lift:.2f}%", f"+{cr_lift:.1f}pp")
    r3.metric("Potential GMV Uplift", f"${uplift_gmv:,.0f}")
    st.info(f"Estimated incremental orders: **{uplift_orders:.0f}**. Estimated GMV uplift: **${uplift_gmv:,.0f}**.")
else:
    with cc1:
        cr_lift = st.number_input("Target lift (percentage points)", value=0.5, min_value=0.0, max_value=50.0, step=0.1, key="bulk_lift")
        st.caption(f"{len(drag_calc)} drag SKUs identified across all historical data.")
    with cc2:
        st.metric("Combined Drag SKU Traffic", f"{drag_calc['total_traffic'].sum():,.0f}")
        st.metric("Average Drag SKU AOV", f"${drag_calc['aov'].mean():,.0f}")

    drag_calc["uplift_gmv"] = drag_calc["total_traffic"] * (cr_lift / 100) * drag_calc["aov"]
    total_uplift = drag_calc["uplift_gmv"].sum()

    st.divider()
    st.metric("Total Potential GMV Uplift", f"${total_uplift:,.0f}")

    top_uplift = drag_calc.sort_values("uplift_gmv", ascending=False).head(10)
    display_df = top_uplift[["product_name", "brand", "total_traffic", "conversion_rate", "aov", "uplift_gmv"]].rename(
        columns={
            "product_name": "Product",
            "brand": "Brand",
            "total_traffic": "Traffic",
            "conversion_rate": "Current Conversion",
            "aov": "AOV",
            "uplift_gmv": "Estimated GMV Uplift",
        }
    )
    display_df["Current Conversion"] = (display_df["Current Conversion"] * 100).round(2).astype(str) + "%"
    display_df["Estimated GMV Uplift"] = display_df["Estimated GMV Uplift"].round(0)
    st.caption("Top 10 drag SKUs by estimated uplift")
    st.dataframe(display_df, use_container_width=True, hide_index=True)

st.divider()

st.subheader("📈 Follow-up Tracking")
tracking_table = pd.DataFrame(
    [
        ["Optimize drag SKU title, image, and offer", "CTR, conversion rate, GMV, refund rate", "7-14 days"],
        ["Adjust price and discount depth", "Conversion rate, AOV, gross margin, GMV", "7-14 days"],
        ["Increase exposure for potential SKUs", "Traffic, CTR, conversion rate, GMV contribution", "7 days"],
        ["Rebalance campaign resources", "Campaign ROI, GMV, order volume", "Campaign period"],
        ["Track AI recommendation adoption", "Adoption rate, action completion, report cycle time", "Weekly review"],
    ],
    columns=["Strategy", "Metrics", "Cadence"],
)
st.dataframe(tracking_table, use_container_width=True, hide_index=True)

with st.expander("💬 Ask a follow-up data question"):
    user_q = st.text_input("Example: Which brand has the highest share of drag SKUs?")
    ask_btn = st.button("Ask")
    if ask_btn and user_q:
        if not api_key:
            st.error("Please enter an API key first.")
        else:
            with st.spinner("Answering from the current data context..."):
                try:
                    from anthropic import Anthropic

                    client = Anthropic(api_key=api_key)
                    data_context = build_data_context(report_scope, scope_value, window_start, max_date)
                    if data_context is None:
                        st.warning("No data is available for the selected scope and time window.")
                        st.stop()
                    message = client.messages.create(
                        model="claude-sonnet-4-5",
                        max_tokens=800,
                        system=SYSTEM_PROMPT + "\nIf the user asks a narrow follow-up, answer directly instead of returning the six-section report.",
                        messages=[{"role": "user", "content": f"Data context:\n{data_context}\n\nQuestion: {user_q}"}],
                    )
                    st.markdown(message.content[0].text)
                except Exception as exc:
                    st.error(f"Answer generation failed: {exc}")
