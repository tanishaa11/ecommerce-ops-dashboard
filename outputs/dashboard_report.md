# E-Commerce Ops Dashboard
**Generated:** 2026-06-13 06:48
**Source:** Single unified pipeline replacing 3 manual trackers

---

## Executive KPIs

| Metric | Value |
|--------|-------|
| Total Orders | 30 |
| Unique Customers | 21 |
| Total Revenue | ₹397,894 |
| Net Revenue | ₹391,814 |
| Avg Discount | 6.37% |
| Return Rate | 13.33% |

---

## Monthly Revenue Trend

| Month | Orders | Gross Revenue | Net Revenue | Return Rate |
|-------|--------|--------------|-------------|-------------|
| 2024-01 | 10 | ₹118,682 | ₹116,622 | 10.0% |
| 2024-02 | 10 | ₹147,816 | ₹145,536 | 20.0% |
| 2024-03 | 10 | ₹131,396 | ₹129,656 | 10.0% |

**Best month:** 2024-02  |  **Weakest month:** 2024-01

---

## Top 10 Products by Net Revenue

| Product | Category | Units | Gross | Net |
|---------|----------|-------|-------|-----|
| Ergonomic Chair | Furniture | 14 | ₹104,975 | ₹103,625 |
| Standing Desk | Furniture | 9 | ₹100,500 | ₹99,300 |
| Wireless Headphones | Electronics | 14 | ₹37,524 | ₹37,044 |
| Air Fryer Pro | Appliances | 6 | ₹36,851 | ₹36,101 |
| Running Shoes X | Sports | 8 | ₹25,893 | ₹25,593 |
| Noise Cancel Buds | Electronics | 13 | ₹24,328 | ₹24,088 |
| Office Bookshelf | Furniture | 6 | ₹18,176 | ₹17,576 |
| Coffee Maker Deluxe | Appliances | 4 | ₹16,786 | ₹16,186 |
| Yoga Mat Pro | Sports | 12 | ₹14,679 | ₹14,439 |
| Resistance Bands | Sports | 16 | ₹9,584 | ₹9,464 |

---

## Return Analysis

| Product | Category | Orders | Returns | Return Rate |
|---------|----------|--------|---------|-------------|
| Ergonomic Chair | Furniture | 3 | 1 | 33.33% |
| Running Shoes X | Sports | 3 | 1 | 33.33% |
| Yoga Mat Pro | Sports | 3 | 1 | 33.33% |
| Wireless Headphones | Electronics | 4 | 1 | 25.0% |
| Air Fryer Pro | Appliances | 3 | 0 | 0.0% |
| Coffee Maker Deluxe | Appliances | 3 | 0 | 0.0% |
| Formal Sneakers | Sports | 2 | 0 | 0.0% |
| Noise Cancel Buds | Electronics | 3 | 0 | 0.0% |
| Office Bookshelf | Furniture | 2 | 0 | 0.0% |
| Resistance Bands | Sports | 2 | 0 | 0.0% |
| Standing Desk | Furniture | 2 | 0 | 0.0% |

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
