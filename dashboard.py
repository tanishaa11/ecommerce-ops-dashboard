"""
dashboard.py
─────────────
E-Commerce Ops Dashboard — replaces 3 manual trackers with one pipeline run.

Eliminated trackers:
  1. Revenue & Sales tracker (Excel)  → Query 1 + 2 + 7
  2. Returns & Quality log (Sheet)    → Query 6
  3. Regional sales summary (CSV)     → Query 4

Outputs:
  - outputs/dashboard_report.md  — full SOP-formatted report
  - outputs/charts/              — PNG charts for each KPI section
  - outputs/data/                — clean CSVs for each query result

Usage:
  python dashboard.py
  python dashboard.py --input data/orders.csv
  python dashboard.py --no-charts   # skip matplotlib output
"""

import argparse
import os
import sqlite3
import textwrap
from datetime import datetime
from pathlib import Path

import pandas as pd

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.ticker as mticker
    HAS_MPL = True
except ImportError:
    HAS_MPL = False
    print("[WARN] matplotlib not installed — skipping charts. Run: pip install matplotlib")

OUTPUT_DIR    = Path("outputs")
CHARTS_DIR    = OUTPUT_DIR / "charts"
DATA_DIR      = OUTPUT_DIR / "data"
DB_PATH       = OUTPUT_DIR / "ecommerce.db"

for d in [OUTPUT_DIR, CHARTS_DIR, DATA_DIR]:
    d.mkdir(parents=True, exist_ok=True)


# ── 1. Load CSV → SQLite ──────────────────────────────────────────────────────

def load_to_db(csv_path: str) -> sqlite3.Connection:
    df = pd.read_csv(csv_path, parse_dates=["date"])
    conn = sqlite3.connect(DB_PATH)
    df.to_sql("orders", conn, if_exists="replace", index=False)

    conn.execute("""
        CREATE VIEW IF NOT EXISTS orders_enriched AS
        SELECT *,
            ROUND(units * unit_price * (1 - discount), 2)         AS revenue,
            ROUND(units * unit_price * (1 - discount)
                  - shipping_cost, 2)                              AS net_revenue,
            CASE WHEN returned = 'Yes' THEN 1 ELSE 0 END           AS is_returned,
            STRFTIME('%Y-%m', date)                                 AS month
        FROM orders
    """)
    conn.commit()
    print(f"[✓] Loaded {len(df)} records into SQLite")
    return conn


def q(conn, sql) -> pd.DataFrame:
    return pd.read_sql_query(sql, conn)


# ── 2. Run All Queries ────────────────────────────────────────────────────────

def run_queries(conn) -> dict:
    queries = {
        "kpis": """
            SELECT
                COUNT(DISTINCT order_id)                    AS total_orders,
                COUNT(DISTINCT customer_id)                 AS unique_customers,
                ROUND(SUM(revenue), 2)                      AS total_revenue,
                ROUND(SUM(net_revenue), 2)                  AS total_net_revenue,
                ROUND(AVG(discount)*100, 2)                 AS avg_discount_pct,
                ROUND(SUM(is_returned)*100.0/COUNT(*), 2)   AS return_rate_pct
            FROM orders_enriched
        """,
        "monthly": """
            SELECT month,
                COUNT(order_id)                             AS orders,
                ROUND(SUM(revenue), 2)                      AS revenue,
                ROUND(SUM(net_revenue), 2)                  AS net_revenue,
                ROUND(SUM(is_returned)*100.0/COUNT(*), 2)   AS return_rate_pct
            FROM orders_enriched
            GROUP BY month ORDER BY month
        """,
        "by_category": """
            SELECT category, sub_category,
                COUNT(order_id)                             AS orders,
                SUM(units)                                  AS units_sold,
                ROUND(SUM(revenue), 2)                      AS revenue
            FROM orders_enriched
            GROUP BY category, sub_category ORDER BY revenue DESC
        """,
        "by_region": """
            SELECT region, city,
                COUNT(order_id)                             AS orders,
                ROUND(SUM(revenue), 2)                      AS revenue,
                ROUND(SUM(is_returned)*100.0/COUNT(*), 2)   AS return_rate_pct
            FROM orders_enriched
            GROUP BY region, city ORDER BY revenue DESC
        """,
        "by_segment": """
            SELECT customer_segment,
                COUNT(DISTINCT customer_id)                 AS customers,
                COUNT(order_id)                             AS orders,
                ROUND(SUM(revenue), 2)                      AS revenue,
                ROUND(SUM(revenue)/COUNT(DISTINCT customer_id), 2) AS rev_per_customer
            FROM orders_enriched
            GROUP BY customer_segment ORDER BY revenue DESC
        """,
        "returns": """
            SELECT product_name, category,
                COUNT(order_id)                             AS total_orders,
                SUM(is_returned)                            AS total_returns,
                ROUND(SUM(is_returned)*100.0/COUNT(*), 2)   AS return_rate_pct
            FROM orders_enriched
            GROUP BY product_name, category
            HAVING total_orders > 1
            ORDER BY return_rate_pct DESC
        """,
        "top_products": """
            SELECT product_name, category,
                SUM(units)                                  AS units_sold,
                ROUND(SUM(revenue), 2)                      AS gross_revenue,
                ROUND(SUM(net_revenue), 2)                  AS net_revenue
            FROM orders_enriched
            GROUP BY product_name, category
            ORDER BY net_revenue DESC LIMIT 10
        """,
    }

    results = {}
    for name, sql in queries.items():
        df = q(conn, textwrap.dedent(sql))
        df.to_csv(DATA_DIR / f"{name}.csv", index=False)
        results[name] = df
        print(f"[✓] Query: {name} ({len(df)} rows)")

    return results


# ── 3. Charts ─────────────────────────────────────────────────────────────────

TEAL   = "#1D9E75"
NAVY   = "#185FA5"
AMBER  = "#EF9F27"
CORAL  = "#D85A30"
GRAY   = "#888780"

def save_chart(fig, name):
    path = CHARTS_DIR / f"{name}.png"
    fig.savefig(path, bbox_inches="tight", dpi=150, facecolor="white")
    plt.close(fig)
    print(f"[✓] Chart saved → {path}")

def make_charts(results: dict):
    if not HAS_MPL:
        return

    # Monthly revenue bar
    monthly = results["monthly"]
    fig, ax = plt.subplots(figsize=(8, 3.5))
    bars = ax.bar(monthly["month"], monthly["revenue"]/1000, color=TEAL, width=0.5)
    ax.bar(monthly["month"], monthly["net_revenue"]/1000, color=NAVY, width=0.3, label="Net revenue")
    ax.set_title("Monthly Revenue (₹000)", fontsize=12, fontweight="bold", pad=10)
    ax.set_ylabel("₹ (thousands)")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"₹{x:,.0f}K"))
    ax.tick_params(axis="x", rotation=15)
    ax.spines[["top","right"]].set_visible(False)
    ax.legend(["Gross revenue", "Net revenue"], fontsize=9)
    save_chart(fig, "monthly_revenue")

    # Category donut
    cat = results["by_category"].groupby("category")["revenue"].sum().sort_values()
    fig, ax = plt.subplots(figsize=(5, 4))
    wedges, texts, autotexts = ax.pie(
        cat.values, labels=cat.index,
        autopct="%1.1f%%", startangle=140,
        colors=[TEAL, NAVY, AMBER, CORAL, GRAY],
        wedgeprops={"width": 0.55}
    )
    ax.set_title("Revenue by Category", fontsize=12, fontweight="bold")
    save_chart(fig, "revenue_by_category")

    # Regional bar
    region = results["by_region"].groupby("region")["revenue"].sum().sort_values()
    fig, ax = plt.subplots(figsize=(6, 3))
    ax.barh(region.index, region.values/1000, color=AMBER)
    ax.set_title("Revenue by Region (₹000)", fontsize=12, fontweight="bold", pad=10)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"₹{x:,.0f}K"))
    ax.spines[["top","right"]].set_visible(False)
    save_chart(fig, "revenue_by_region")

    # Return rate bar
    ret = results["returns"].head(8)
    fig, ax = plt.subplots(figsize=(7, 3.5))
    colors = [CORAL if r > 20 else AMBER if r > 10 else TEAL for r in ret["return_rate_pct"]]
    ax.barh(ret["product_name"], ret["return_rate_pct"], color=colors)
    ax.set_title("Return Rate by Product (%)", fontsize=12, fontweight="bold", pad=10)
    ax.set_xlabel("Return rate %")
    ax.spines[["top","right"]].set_visible(False)
    save_chart(fig, "return_rates")

    # Segment revenue
    seg = results["by_segment"]
    fig, ax = plt.subplots(figsize=(5, 3))
    ax.bar(seg["customer_segment"], seg["revenue"]/1000, color=[TEAL, NAVY, AMBER])
    ax.set_title("Revenue by Customer Segment (₹000)", fontsize=11, fontweight="bold", pad=10)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"₹{x:,.0f}K"))
    ax.spines[["top","right"]].set_visible(False)
    save_chart(fig, "segment_revenue")


# ── 4. Report + SOP ───────────────────────────────────────────────────────────

def build_report(results: dict) -> str:
    kpi = results["kpis"].iloc[0]
    monthly = results["monthly"]
    top = results["top_products"]
    ret = results["returns"]

    best_month  = monthly.loc[monthly["revenue"].idxmax(), "month"]
    worst_month = monthly.loc[monthly["revenue"].idxmin(), "month"]

    product_table = "\n".join(
        f"| {r.product_name} | {r.category} | {int(r.units_sold):,} | ₹{r.gross_revenue:,.0f} | ₹{r.net_revenue:,.0f} |"
        for _, r in top.iterrows()
    )

    return_table = "\n".join(
        f"| {r.product_name} | {r.category} | {int(r.total_orders)} | {int(r.total_returns)} | {r.return_rate_pct}% |"
        for _, r in ret.iterrows()
    )

    return f"""# E-Commerce Ops Dashboard
**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M")}
**Source:** Single unified pipeline replacing 3 manual trackers

---

## Executive KPIs

| Metric | Value |
|--------|-------|
| Total Orders | {int(kpi.total_orders):,} |
| Unique Customers | {int(kpi.unique_customers):,} |
| Total Revenue | ₹{kpi.total_revenue:,.0f} |
| Net Revenue | ₹{kpi.total_net_revenue:,.0f} |
| Avg Discount | {kpi.avg_discount_pct}% |
| Return Rate | {kpi.return_rate_pct}% |

---

## Monthly Revenue Trend

| Month | Orders | Gross Revenue | Net Revenue | Return Rate |
|-------|--------|--------------|-------------|-------------|
""" + "\n".join(
        f"| {r.month} | {int(r.orders)} | ₹{r.revenue:,.0f} | ₹{r.net_revenue:,.0f} | {r.return_rate_pct}% |"
        for _, r in monthly.iterrows()
    ) + f"""

**Best month:** {best_month}  |  **Weakest month:** {worst_month}

---

## Top 10 Products by Net Revenue

| Product | Category | Units | Gross | Net |
|---------|----------|-------|-------|-----|
{product_table}

---

## Return Analysis

| Product | Category | Orders | Returns | Return Rate |
|---------|----------|--------|---------|-------------|
{return_table}

---

## How to Use This Dashboard (SOP)

**Step 1 — Update data**
Replace `data/orders.csv` with your latest export. Same column headers required.

**Step 2 — Run pipeline**
```bash
python dashboard.py
```

**Step 3 — Review outputs**
- `outputs/dashboard_report.md` — full report for sharing with stakeholders
- `outputs/charts/` — PNG charts ready for slide decks or Notion pages
- `outputs/data/*.csv` — clean query outputs for further analysis

**Step 4 — Share with team**
Non-technical stakeholders: share the Markdown report or paste charts into Notion/Slides.
No analyst support required to interpret — all KPIs are labelled and self-explanatory.

---

*Dashboard: ecommerce-ops-dashboard · Queries: SQLite · Charts: Matplotlib*
"""


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="E-Commerce Ops Dashboard")
    parser.add_argument("--input",     default="data/orders.csv")
    parser.add_argument("--no-charts", action="store_true")
    args = parser.parse_args()

    print("\n── E-Commerce Ops Dashboard ──────────────────────")
    print("Stage 1/4  Loading data into SQLite...")
    conn = load_to_db(args.input)

    print("Stage 2/4  Running queries...")
    results = run_queries(conn)

    if not args.no_charts:
        print("Stage 3/4  Generating charts...")
        make_charts(results)
    else:
        print("Stage 3/4  [SKIP] Charts disabled")

    print("Stage 4/4  Writing report + SOP...")
    report = build_report(results)
    report_path = OUTPUT_DIR / "dashboard_report.md"
    report_path.write_text(report, encoding="utf-8")

    print(f"\n[✓] Dashboard complete → {OUTPUT_DIR}/")
    print("     dashboard_report.md  — stakeholder report")
    print("     charts/              — 5 PNG charts")
    print("     data/                — 7 clean CSV exports")
    print("─────────────────────────────────────────────────\n")


if __name__ == "__main__":
    main()
