def build_third_sql_map(table_name: str) -> dict[str, str]:
    t = f"cr_kpi.{table_name}"
    return {
        "q1": f"""
SELECT
    rgn,
    outlet_category,
    outlet_type,
    sales_outlet,
    rate_performance,
    rate_quality,
    total_score,
    new_car_reg_pct,
    gear_up_ach_pct,
    ins_renew_1st_pct,
    ins_renew_overall_pct,
    pov_pct,
    intake_pct,
    revenue_pct,
    parts_pct,
    lubricant_pct,
    cs_sales_pct,
    nps_sales_pct,
    eappointment_pct,
    qpi_pct,
    cs_service_pct
FROM {t}
WHERE rgn IS NOT NULL AND outlet_category IN ('B', 'C', 'D');
""",
        "q2": f"""   
WITH category_avg AS (
    SELECT
        outlet_category,
        AVG(new_car_reg_pct - 100) AS gap_new_car_reg,
        AVG(gear_up_ach_pct - 100) AS gap_gear_up,
        AVG(ins_renew_1st_pct - 100) AS gap_ins_renew_1st,
        AVG(ins_renew_overall_pct - 100) AS gap_ins_renew_overall,
        AVG(pov_pct - 100) AS gap_pov,
        AVG(intake_pct - 100) AS gap_intake,
        AVG(revenue_pct - 100) AS gap_revenue,
        AVG(parts_pct - 100) AS gap_parts,
        AVG(lubricant_pct - 100) AS gap_lubricant,
        AVG(cs_sales_pct - 100) AS gap_cs_sales,
        AVG(nps_sales_pct - 100) AS gap_nps_sales,
        AVG(eappointment_pct - 100) AS gap_eappointment,
        AVG(qpi_pct - 100) AS gap_qpi,
        AVG(cs_service_pct - 100) AS gap_cs_service
    FROM {t}
    WHERE outlet_category IN ('B', 'C', 'D')
    GROUP BY outlet_category
)
SELECT outlet_category, 'New Car Reg' AS kpi, gap_new_car_reg AS gap_value FROM category_avg
UNION ALL
SELECT outlet_category, 'Gear Up' AS kpi, gap_gear_up AS gap_value FROM category_avg
UNION ALL
SELECT outlet_category, 'Ins Renew 1st' AS kpi, gap_ins_renew_1st AS gap_value FROM category_avg
UNION ALL
SELECT outlet_category, 'Ins Renew Overall' AS kpi, gap_ins_renew_overall AS gap_value FROM category_avg
UNION ALL
SELECT outlet_category, 'POV' AS kpi, gap_pov AS gap_value FROM category_avg
UNION ALL
SELECT outlet_category, 'Intake' AS kpi, gap_intake AS gap_value FROM category_avg
UNION ALL
SELECT outlet_category, 'Revenue' AS kpi, gap_revenue AS gap_value FROM category_avg
UNION ALL
SELECT outlet_category, 'Parts' AS kpi, gap_parts AS gap_value FROM category_avg
UNION ALL
SELECT outlet_category, 'Lubricant' AS kpi, gap_lubricant AS gap_value FROM category_avg
UNION ALL
SELECT outlet_category, 'CS Sales' AS kpi, gap_cs_sales AS gap_value FROM category_avg
UNION ALL
SELECT outlet_category, 'NPS Sales' AS kpi, gap_nps_sales AS gap_value FROM category_avg
UNION ALL
SELECT outlet_category, 'eAppointment' AS kpi, gap_eappointment AS gap_value FROM category_avg
UNION ALL
SELECT outlet_category, 'QPI' AS kpi, gap_qpi AS gap_value FROM category_avg
UNION ALL
SELECT outlet_category, 'CS Service' AS kpi, gap_cs_service AS gap_value FROM category_avg
ORDER BY outlet_category, kpi;
""",
        "radar-chart-before-filtering-q2": f"""
SELECT 
    outlet_type,
    -- Sales-focused KPIs: zero for 2S (service-only)
    AVG(CASE WHEN outlet_type = '2S' THEN 0 ELSE new_car_reg_pct END) AS avg_new_car_reg,
    AVG(CASE WHEN outlet_type = '2S' THEN 0 ELSE gear_up_ach_pct END) AS avg_gear_up,
    AVG(CASE WHEN outlet_type = '2S' THEN 0 ELSE ins_renew_1st_pct END) AS avg_ins_renew_1st,
    AVG(CASE WHEN outlet_type = '2S' THEN 0 ELSE ins_renew_overall_pct END) AS avg_ins_renew_overall,
    AVG(CASE WHEN outlet_type = '2S' THEN 0 ELSE pov_pct END) AS avg_pov,
    AVG(CASE WHEN outlet_type = '2S' THEN 0 ELSE nps_sales_pct END) AS avg_nps_sales,
    AVG(CASE WHEN outlet_type = '2S' THEN 0 ELSE cs_sales_pct END) AS avg_cs_sales,
    -- Service-focused KPIs: zero for 1S (sales-only)
    AVG(CASE WHEN outlet_type = '1S' THEN 0 ELSE intake_pct END) AS avg_intake,
    AVG(CASE WHEN outlet_type = '1S' THEN 0 ELSE revenue_pct END) AS avg_revenue,
    AVG(CASE WHEN outlet_type = '1S' THEN 0 ELSE parts_pct END) AS avg_parts,
    AVG(CASE WHEN outlet_type = '1S' THEN 0 ELSE lubricant_pct END) AS avg_lubricant,
    AVG(CASE WHEN outlet_type = '1S' THEN 0 ELSE eappointment_pct END) AS avg_eappointment,
    AVG(CASE WHEN outlet_type = '1S' THEN 0 ELSE qpi_pct END) AS avg_qpi,
    AVG(CASE WHEN outlet_type = '1S' THEN 0 ELSE cs_service_pct END) AS avg_cs_service
FROM {t}
WHERE outlet_type IS NOT NULL
GROUP BY outlet_type
ORDER BY outlet_type;
""",
        "radar-chart-after-filtering-q3": f"""
SELECT 
    outlet_type,
    outlet_category,
    -- Sales-focused KPIs: zero for 2S (service-only)
    AVG(CASE WHEN outlet_type = '2S' THEN 0 ELSE new_car_reg_pct END) AS avg_new_car_reg,
    AVG(CASE WHEN outlet_type = '2S' THEN 0 ELSE gear_up_ach_pct END) AS avg_gear_up,
    AVG(CASE WHEN outlet_type = '2S' THEN 0 ELSE ins_renew_1st_pct END) AS avg_ins_renew_1st,
    AVG(CASE WHEN outlet_type = '2S' THEN 0 ELSE ins_renew_overall_pct END) AS avg_ins_renew_overall,
    AVG(CASE WHEN outlet_type = '2S' THEN 0 ELSE pov_pct END) AS avg_pov,
    AVG(CASE WHEN outlet_type = '2S' THEN 0 ELSE nps_sales_pct END) AS avg_nps_sales,
    AVG(CASE WHEN outlet_type = '2S' THEN 0 ELSE cs_sales_pct END) AS avg_cs_sales,
    -- Service-focused KPIs: zero for 1S (sales-only)
    AVG(CASE WHEN outlet_type = '1S' THEN 0 ELSE intake_pct END) AS avg_intake,
    AVG(CASE WHEN outlet_type = '1S' THEN 0 ELSE revenue_pct END) AS avg_revenue,
    AVG(CASE WHEN outlet_type = '1S' THEN 0 ELSE parts_pct END) AS avg_parts,
    AVG(CASE WHEN outlet_type = '1S' THEN 0 ELSE lubricant_pct END) AS avg_lubricant,
    AVG(CASE WHEN outlet_type = '1S' THEN 0 ELSE eappointment_pct END) AS avg_eappointment,
    AVG(CASE WHEN outlet_type = '1S' THEN 0 ELSE qpi_pct END) AS avg_qpi,
    AVG(CASE WHEN outlet_type = '1S' THEN 0 ELSE cs_service_pct END) AS avg_cs_service
FROM {t}
WHERE outlet_type IS NOT NULL
    AND outlet_category IS NOT NULL
GROUP BY outlet_type, outlet_category
ORDER BY outlet_type, outlet_category;""",
    }
