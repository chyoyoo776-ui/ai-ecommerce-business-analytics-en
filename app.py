# -*- coding: utf-8 -*-
"""Main entry point for the AI e-commerce business analytics dashboard."""

import streamlit as st


st.set_page_config(
    page_title="AI E-commerce Business Analytics",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🛍️ AI E-commerce Business Analytics")
st.caption("A portfolio-ready operating dashboard and AI strategy assistant for e-commerce decision making.")

st.markdown("### 🎯 Business Problem")
st.info(
    "When GMV declines, a standard BI dashboard can show revenue, traffic, and conversion movement, "
    "but it often cannot explain whether the issue is traffic quality, product conversion, pricing, "
    "inventory, or a small group of underperforming SKUs. This project turns that diagnostic workflow "
    "into an interactive analytics product."
)

st.markdown("### 🔗 Analytical Workflow")
st.markdown(
    """
1. **Business Question**: What is driving GMV movement?
2. **KPI Framework**: Decompose GMV into traffic, conversion rate, orders, and average order value.
3. **Anomaly Detection**: Compare the selected period with the previous equal-length period.
4. **Root Cause Analysis**: Identify channel, campaign, and SKU-level issues.
5. **Strategic Recommendations**: Generate structured action plans with an AI strategy assistant.
6. **Expected Business Impact**: Estimate GMV upside from conversion-rate improvement.
7. **Follow-up Tracking**: Define metrics and A/B tests to validate the recommendation.
"""
)

st.markdown("### 📖 Dashboard Pages")

with st.container(border=True):
    st.markdown(
        """
**📊 Business Overview**

Monitor operating health across GMV, traffic, conversion rate, AOV, order volume, refund rate, and channel performance.
"""
    )

with st.container(border=True):
    st.markdown(
        """
**🔍 Product Diagnosis**

Segment SKUs using a traffic-by-conversion framework and identify high-traffic, low-conversion products that are likely wasting exposure.
"""
    )

with st.container(border=True):
    st.markdown(
        """
**🤖 AI Strategy Assistant**

Convert observed anomalies and product diagnosis results into strategic recommendations, expected impact, tracking metrics, and A/B test plans.
"""
    )

st.divider()

col_a, col_b = st.columns(2)
with col_a:
    st.markdown(
        """
### Data Background

The dataset simulates a flash-sale e-commerce marketplace across Sports & Outdoor and Footwear categories.
It covers 21 brands, synthetic order and traffic behavior from December 2024 through December 2025,
and realistic business dynamics including campaign peaks, seasonality, channel mix, pricing, inventory, and refund risk.

All data is synthetic and does not represent any real company.
"""
    )
with col_b:
    st.markdown(
        """
### Technical Stack

- Streamlit for the interactive dashboard
- Pandas for data modeling and aggregation
- Plotly for business charts
- Anthropic Claude API for optional strategy generation
"""
    )

with st.sidebar:
    st.header("Project Scope")
    st.markdown(
        """
**Data Period**  
2024-12 to 2025-12

**Categories**  
Sports & Outdoor, Footwear

**Brand Universe**  
21 brands
"""
    )
