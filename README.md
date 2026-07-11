# AI E-commerce Business Analytics Dashboard

A Streamlit portfolio project that simulates an e-commerce flash-sale marketplace and turns operating data into a practical business analytics workflow for recruiters, interviewers, and analytics stakeholders.

## Project Background

This project models a fictional marketplace with 21 portfolio brands across two categories: Sports & Outdoor and Footwear. The synthetic dataset covers December 2024 through December 2025 and includes daily channel performance, campaign-level performance, SKU-level performance, and product catalog attributes.

The dashboard is designed around a realistic business question:

**When GMV changes, what is driving the movement, what should the business do next, and how should the impact be measured?**

## Business Analytics Workflow

The product follows this end-to-end chain:

Business Question -> KPI Framework -> Anomaly Detection -> Root Cause Analysis -> Strategic Recommendation -> Expected Impact -> Follow-up Tracking

## KPI Framework

The core operating model decomposes GMV into:

```text
GMV = Traffic x Conversion Rate x Average Order Value
```

The dashboard also tracks order volume, refund rate, sell-through rate, click-through rate, discount rate, new customer ratio, and campaign mix.

## Dashboard Structure

### Page 1: Business Overview / Operating Health Check

This page monitors platform health across GMV, traffic, conversion rate, average order value, orders, refund rate, and channel performance.

Key logic:

- Compares the selected period with the previous equal-length period.
- Flags material movement in GMV, conversion rate, AOV, traffic, and orders.
- Detects traffic-conversion mismatch when traffic grows but orders do not follow.
- Links high-traffic, low-conversion SKU signals back to product diagnosis.

### Page 2: Product Diagnosis

This page segments SKUs using a traffic-by-conversion matrix.

Segments:

- **Drag SKUs**: high traffic, low conversion.
- **Star SKUs**: high traffic, high conversion.
- **Potential SKUs**: low traffic, high conversion.
- **Edge SKUs**: low traffic, low conversion.

The priority segment is Drag SKUs because those products already receive exposure but fail to convert it. The diagnosis layer uses price flags, listing-quality flags, click-through rate, refund rate, inventory, and sell-through rate to suggest likely root causes.

### Page 3: AI Strategy Assistant

This page converts diagnostic outputs into a structured strategy report.

The assistant follows a fixed business review format:

1. Key Business Issue
2. Root Cause Hypothesis
3. Priority Actions
4. Expected Business Impact
5. Metrics to Track
6. Suggested A/B Test

The page also includes a GMV impact calculator:

```text
Potential GMV Uplift = Traffic x Conversion-Rate Lift x Average Order Value
```

## Data Structure

```text
.
├── app.py
├── utils.py
├── requirements.txt
├── generate_data.py
├── data/
│   ├── daily_business.csv
│   ├── brand_campaigns.csv
│   ├── sku_performance.csv
│   └── product_catalog.csv
└── pages/
    ├── 1_Business_Overview.py
    ├── 2_Product_Diagnosis.py
    └── 3_AI_Strategy_Assistant.py
```

### Data Files

- `daily_business.csv`: daily channel-level traffic, orders, GMV, conversion rate, AOV, refund rate, and promotion flags.
- `brand_campaigns.csv`: campaign-level brand performance, campaign type, promotion name, traffic, GMV, conversion rate, AOV, and new customer ratio.
- `sku_performance.csv`: SKU-by-campaign performance with traffic, CTR, conversion, orders, GMV, discount rate, inventory, sell-through, refund risk, and diagnosis flags.
- `product_catalog.csv`: product master data with fictional brand, category, subcategory, price tier, and listing-quality flags.

All data is synthetic. It is generated to mimic realistic business patterns such as seasonality, promotion peaks, channel mix, pricing differences, inventory pressure, and refund risk. It does not contain real company data.

## How to Run Locally

Install dependencies:

```bash
pip install -r requirements.txt
```

Launch the app:

```bash
streamlit run app.py
```

The app should open at:

```text
http://localhost:8501
```

## Optional Anthropic API Key

The AI Strategy Assistant can run with an Anthropic API key.

For local testing, create a local Streamlit secrets file:

```text
.streamlit/secrets.toml
```

Add:

```toml
ANTHROPIC_API_KEY = "your_api_key_here"
```

Do not commit real API keys. The repository includes only `secrets.toml.example`.

## Portfolio Value

This project demonstrates:

- Business-first KPI design and decomposition.
- Period-over-period operating health checks.
- SKU-level root cause analysis.
- E-commerce merchandising and campaign analytics.
- Productized AI strategy generation.
- Impact sizing and follow-up experiment design.
- Clean Streamlit implementation using Pandas and Plotly.
