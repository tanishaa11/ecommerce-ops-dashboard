-- ============================================================
-- ecommerce_ops_dashboard.sql
-- Single source of truth queries replacing 3 manual trackers:
--   Tracker 1: Revenue & Sales tracker (Excel)
--   Tracker 2: Returns & Quality log (Google Sheet)
--   Tracker 3: Regional sales summary (manual CSV)
-- ============================================================


-- ── TABLE SETUP (SQLite-compatible) ──────────────────────────────────────────

CREATE TABLE IF NOT EXISTS orders (
    order_id         TEXT PRIMARY KEY,
    date             DATE,
    customer_id      TEXT,
    customer_segment TEXT,
    product_id       TEXT,
    product_name     TEXT,
    category         TEXT,
    sub_category     TEXT,
    region           TEXT,
    city             TEXT,
    units            INTEGER,
    unit_price       REAL,
    discount         REAL,
    shipping_cost    REAL,
    returned         TEXT
);


-- ── COMPUTED COLUMNS VIEW ────────────────────────────────────────────────────

CREATE VIEW IF NOT EXISTS orders_enriched AS
SELECT
    *,
    ROUND(units * unit_price * (1 - discount), 2)          AS revenue,
    ROUND(units * unit_price * (1 - discount)
          - shipping_cost, 2)                               AS net_revenue,
    CASE WHEN returned = 'Yes' THEN 1 ELSE 0 END            AS is_returned,
    STRFTIME('%Y-%m', date)                                  AS month
FROM orders;


-- ── QUERY 1: Overall KPIs (replaces Tracker 1 manual summary row) ────────────

SELECT
    COUNT(DISTINCT order_id)              AS total_orders,
    COUNT(DISTINCT customer_id)           AS unique_customers,
    ROUND(SUM(revenue), 2)                AS total_revenue,
    ROUND(SUM(net_revenue), 2)            AS total_net_revenue,
    ROUND(AVG(discount) * 100, 2)         AS avg_discount_pct,
    ROUND(SUM(is_returned) * 100.0
          / COUNT(*), 2)                  AS return_rate_pct
FROM orders_enriched;


-- ── QUERY 2: Monthly Revenue Trend ───────────────────────────────────────────

SELECT
    month,
    COUNT(order_id)                       AS orders,
    ROUND(SUM(revenue), 2)                AS revenue,
    ROUND(SUM(net_revenue), 2)            AS net_revenue,
    ROUND(SUM(is_returned) * 100.0
          / COUNT(*), 2)                  AS return_rate_pct
FROM orders_enriched
GROUP BY month
ORDER BY month;


-- ── QUERY 3: Revenue by Category & Sub-Category ──────────────────────────────

SELECT
    category,
    sub_category,
    COUNT(order_id)                       AS orders,
    SUM(units)                            AS units_sold,
    ROUND(SUM(revenue), 2)                AS revenue,
    ROUND(SUM(revenue) * 100.0
          / SUM(SUM(revenue)) OVER (), 2) AS revenue_share_pct
FROM orders_enriched
GROUP BY category, sub_category
ORDER BY revenue DESC;


-- ── QUERY 4: Regional Breakdown (replaces Tracker 3) ─────────────────────────

SELECT
    region,
    city,
    COUNT(order_id)                       AS orders,
    ROUND(SUM(revenue), 2)                AS revenue,
    ROUND(SUM(net_revenue), 2)            AS net_revenue,
    ROUND(SUM(is_returned) * 100.0
          / COUNT(*), 2)                  AS return_rate_pct
FROM orders_enriched
GROUP BY region, city
ORDER BY revenue DESC;


-- ── QUERY 5: Customer Segment Performance ────────────────────────────────────

SELECT
    customer_segment,
    COUNT(DISTINCT customer_id)           AS customers,
    COUNT(order_id)                       AS orders,
    ROUND(SUM(revenue), 2)                AS revenue,
    ROUND(SUM(revenue)
          / COUNT(DISTINCT customer_id),2) AS revenue_per_customer
FROM orders_enriched
GROUP BY customer_segment
ORDER BY revenue DESC;


-- ── QUERY 6: Return Analysis (replaces Tracker 2) ────────────────────────────

SELECT
    product_name,
    category,
    COUNT(order_id)                       AS total_orders,
    SUM(is_returned)                      AS total_returns,
    ROUND(SUM(is_returned) * 100.0
          / COUNT(*), 2)                  AS return_rate_pct,
    ROUND(SUM(CASE WHEN returned='Yes'
              THEN revenue ELSE 0 END),2) AS returned_revenue
FROM orders_enriched
GROUP BY product_name, category
HAVING total_orders > 1
ORDER BY return_rate_pct DESC;


-- ── QUERY 7: Top 10 Products by Net Revenue ───────────────────────────────────

SELECT
    product_name,
    category,
    SUM(units)                            AS units_sold,
    ROUND(SUM(revenue), 2)                AS gross_revenue,
    ROUND(SUM(net_revenue), 2)            AS net_revenue
FROM orders_enriched
GROUP BY product_name, category
ORDER BY net_revenue DESC
LIMIT 10;
