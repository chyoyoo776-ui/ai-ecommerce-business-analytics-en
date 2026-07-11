# -*- coding: utf-8 -*-
"""Data loading and formatting helpers for the portfolio dashboard."""

from pathlib import Path

import pandas as pd
import streamlit as st


DATA_DIR = Path(__file__).parent / "data"


@st.cache_data
def load_daily_business():
    return pd.read_csv(DATA_DIR / "daily_business.csv", parse_dates=["date"])


@st.cache_data
def load_brand_campaigns():
    return pd.read_csv(
        DATA_DIR / "brand_campaigns.csv",
        parse_dates=["start_date", "end_date"],
    )


@st.cache_data
def load_sku_performance():
    return pd.read_csv(
        DATA_DIR / "sku_performance.csv",
        parse_dates=["start_date", "end_date"],
    )


@st.cache_data
def load_product_catalog():
    return pd.read_csv(DATA_DIR / "product_catalog.csv")


def fmt_revenue(value):
    return f"${value / 1000:,.1f}K"


def fmt_pct(value):
    return f"{value * 100:.2f}%"


def pct_delta(current, previous):
    if previous == 0 or pd.isna(previous):
        return None
    return (current - previous) / previous
