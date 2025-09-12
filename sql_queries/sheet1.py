first_sql_map = {
    "scatter-plot-q1": """SELECT 
    rgn,
    outlet_category,
    sales_outlet,
    rate_performance,
    rate_quality,
    total_score
FROM master.cr_kpi.kpi_outlet
WHERE rgn IS NOT NULL 
    AND outlet_category IS NOT NULL
    AND rate_performance IS NOT NULL
    AND rate_quality IS NOT NULL;""",
    "bar-chart-q2": """SELECT 
    outlet_category,
    COUNT(*) AS outlet_count
FROM master.cr_kpi.kpi_outlet
WHERE outlet_category IS NOT NULL
GROUP BY outlet_category
ORDER BY outlet_category;""",
    "stack-bar-chart-q3": """SELECT 
    rgn,
    outlet_category,
    COUNT(*) AS outlet_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY rgn), 2) AS percentage
FROM master.cr_kpi.kpi_outlet
WHERE rgn IS NOT NULL 
    AND outlet_category IS NOT NULL
GROUP BY rgn, outlet_category
ORDER BY rgn, outlet_category;""",
}
