-- Sales Performance & Business Insights Dashboard
-- SQLite-compatible. Import data/processed/clean_sales.csv as table clean_sales.
-- Revenue is Quantity * UnitPrice. Dataset currency is GBP (pounds sterling).

-- 1. Executive KPIs
SELECT ROUND(SUM(Revenue),2) AS total_revenue_gbp,
       COUNT(DISTINCT InvoiceNo) AS total_orders,
       COUNT(DISTINCT CustomerID) AS known_customers,
       ROUND(SUM(Revenue)/COUNT(DISTINCT InvoiceNo),2) AS average_order_value_gbp,
       SUM(Quantity) AS units_sold
FROM clean_sales;

-- 2. Monthly sales trend
SELECT strftime('%Y-%m', InvoiceDate) AS year_month,
       ROUND(SUM(Revenue),2) AS revenue_gbp,
       COUNT(DISTINCT InvoiceNo) AS orders,
       SUM(Quantity) AS units_sold
FROM clean_sales GROUP BY year_month ORDER BY year_month;

-- 3. Month-over-month change (SQLite window function)
WITH monthly AS (
  SELECT strftime('%Y-%m', InvoiceDate) AS year_month, SUM(Revenue) AS revenue
  FROM clean_sales GROUP BY year_month
), compare_months AS (
  SELECT year_month, revenue,
         LAG(revenue) OVER (ORDER BY year_month) AS previous_month_revenue
  FROM monthly
)
SELECT year_month, ROUND(revenue,2) AS revenue_gbp,
       ROUND(previous_month_revenue,2) AS previous_month_gbp,
       ROUND(100.0*(revenue-previous_month_revenue)/NULLIF(previous_month_revenue,0),2) AS mom_change_pct
FROM compare_months ORDER BY year_month;

-- 4. Top 10 products by revenue
SELECT StockCode, Description, ROUND(SUM(Revenue),2) AS revenue_gbp,
       SUM(Quantity) AS units_sold, COUNT(DISTINCT InvoiceNo) AS orders
FROM clean_sales GROUP BY StockCode, Description
ORDER BY revenue_gbp DESC LIMIT 10;

-- 5. Country performance
SELECT Country, ROUND(SUM(Revenue),2) AS revenue_gbp,
       COUNT(DISTINCT InvoiceNo) AS orders,
       COUNT(DISTINCT CustomerID) AS known_customers
FROM clean_sales GROUP BY Country ORDER BY revenue_gbp DESC;

-- 6. Customer value (descriptive, not predictive)
SELECT CustomerID, ROUND(SUM(Revenue),2) AS lifetime_revenue_gbp,
       COUNT(DISTINCT InvoiceNo) AS orders,
       ROUND(SUM(Revenue)/COUNT(DISTINCT InvoiceNo),2) AS avg_order_value_gbp
FROM clean_sales WHERE CustomerID IS NOT NULL
GROUP BY CustomerID ORDER BY lifetime_revenue_gbp DESC LIMIT 20;

-- 7. Day-of-week pattern
SELECT CASE CAST(strftime('%w', InvoiceDate) AS INTEGER)
         WHEN 0 THEN 'Sunday' WHEN 1 THEN 'Monday' WHEN 2 THEN 'Tuesday'
         WHEN 3 THEN 'Wednesday' WHEN 4 THEN 'Thursday' WHEN 5 THEN 'Friday' ELSE 'Saturday' END AS weekday,
       ROUND(SUM(Revenue),2) AS revenue_gbp, COUNT(DISTINCT InvoiceNo) AS orders
FROM clean_sales GROUP BY weekday ORDER BY revenue_gbp DESC;

-- 8. Revenue concentration by product (share of revenue)
WITH p AS (SELECT Description, SUM(Revenue) revenue FROM clean_sales GROUP BY Description)
SELECT Description, ROUND(revenue,2) revenue_gbp,
       ROUND(100.0*revenue/(SELECT SUM(revenue) FROM p),2) AS revenue_share_pct
FROM p ORDER BY revenue DESC LIMIT 15;

-- 9. Validate weekday coverage
SELECT
    strftime('%w', InvoiceDate) AS weekday_number,
    COUNT(*) AS sales_rows,
    ROUND(SUM(Revenue), 2) AS revenue_gbp
FROM clean_sales
GROUP BY weekday_number
ORDER BY weekday_number;