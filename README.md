# ⚽ Football Analytics Dashboard

A dark-themed, interactive Streamlit dashboard that accepts any football metrics CSV and auto-generates visualizations.

## Setup

```bash
# 1. Clone / download this folder
cd football-dashboard

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run
streamlit run app.py
```

Then open http://localhost:8501 in your browser.

## Features

| Tab | What you get |
|-----|-------------|
| 📊 Distributions | Histogram / Box / Violin for any metric, coloured by any category |
| 🏆 Rankings | Horizontal bar chart of top-N players/teams; aggregate by category |
| 🔍 Correlation | Scatter plot with optional trendline + full correlation heatmap |
| 📈 Trends | Line charts over time/rounds + radar comparison between players |
| 📋 Data Table | Searchable, filterable table with CSV export |

## CSV Requirements

Any CSV works. The dashboard auto-detects:
- **Numeric columns** → metrics, KPIs, charts
- **Categorical columns** → filters, groupings, colours
- **Date/Season columns** → trend axis

Named columns like `goals`, `assists`, `player`, `team`, `position` are automatically recognised and pre-selected.
