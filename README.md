# 🍬 Nassau Candy Distributor — Route Efficiency Dashboard

A full Streamlit analytics dashboard for analysing factory-to-customer
shipping route efficiency across Nassau Candy Distributor's US operations.

---

## Project Structure

```
nassau_candy/
├── app.py              # Main Streamlit application (all 5 dashboard tabs)
├── data_loader.py      # Data ingestion, cleaning & feature engineering
├── config.py           # Factory coordinates, product→factory map, state centroids
├── requirements.txt    # Python dependencies
└── Nassau_Candy_Distributor.csv   ← place your data file here
```

---

## Setup & Run

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Place your CSV in this folder
  Nassau_Candy_Distributor.csv

# 3. Launch the dashboard
streamlit run app.py
```

---

## Dashboard Tabs

| Tab | Contents |
|-----|----------|
| 📊 Route Efficiency Overview | Top/Bottom 10 routes, full leaderboard, lead-time box plots |
| 🗺️ Geographic Shipping Map | US choropleth heatmap (avg lead time / delay rate / volume), factory pins, regional bubble chart |
| 🚚 Ship Mode Comparison | Avg lead time & delay rate bars, violin distributions, cost-time scatter |
| 🔍 Route Drill-Down | Factory → State selector, monthly trend, product breakdown, all-states bar |
| 📦 Order-Level Timeline | Lead-time histogram, weekly volume/LT dual-axis chart, sortable order table |

---

## Sidebar Filters (Global)

- **Date range** — Order Date window
- **Region** — multi-select
- **State / Province** — multi-select
- **Ship Mode** — multi-select
- **Delay Threshold (days)** — slider (1–30 days); orders above = "Delayed"
- **Product Division** — Chocolate / Sugar / Other

---

## Key KPIs

| KPI | Definition |
|-----|------------|
| Shipping Lead Time | Ship Date − Order Date (days) |
| Average Lead Time | Mean lead time per route |
| Route Volume | # orders per route |
| Delay Rate | % orders exceeding the threshold slider |
| Efficiency Score | Weighted composite: 60 % normalised lead time + 40 % normalised delay rate (0–100, higher = better) |

---

## Factory Locations

| Factory | State | Lat | Lon |
|---------|-------|-----|-----|
| Lot's O' Nuts | AZ | 32.88 | -111.77 |
| Wicked Choccy's | GA | 32.08 | -81.09 |
| Sugar Shack | MN | 48.12 | -96.18 |
| Secret Factory | IL | 41.45 | -90.57 |
| The Other Factory | TN | 35.12 | -89.97 |

---

## Notes on Data

- Rows with unparseable or negative lead times are dropped automatically;
  a count is shown in the sidebar if any are removed.
- Factory assignment is derived from `Product Name` via the lookup in
  `config.py → PRODUCT_FACTORY_MAP`; unknown products fall back to
  Division-level defaults.
- Date fields are parsed with `infer_datetime_format=True` to handle
  mixed format CSVs gracefully.


## 👩‍💻 Author

Aditi Marwadi