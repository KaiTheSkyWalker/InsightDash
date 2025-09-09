third_sql_map = {
    "q1": """
        SELECT 
            rgn,
            AVG(intake_unit) AS avg_intake_units,
            AVG(intake_pct) AS avg_intake_percentage,
            AVG(revenue_pct) AS avg_revenue_performance,
            AVG(parts_pct) AS avg_parts_performance,
            AVG(lubricant_pct) AS avg_lubricant_performance
        FROM master.cr_kpi.kpi_outlet
        GROUP BY rgn
        ORDER BY avg_intake_units DESC;
    """,

    "q2": """
        SELECT 
            outlet_category,
            AVG(intake_unit) AS avg_intake_units,
            AVG(intake_pct) AS avg_intake_percentage,
            AVG(revenue_pct) AS avg_revenue_performance,
            AVG(eappointment_pct) AS avg_eappointment_adoption,
            AVG(qpi_pct) AS avg_quality_performance_index
        FROM master.cr_kpi.kpi_outlet
        GROUP BY outlet_category
        ORDER BY avg_intake_units DESC;
    """,

    "q3": """
        SELECT 
            rgn,
            outlet_category,
            COUNT(*) AS outlet_count,
            AVG(cs_service_pct) AS avg_customer_satisfaction_service,
            AVG(rate_performance) AS avg_performance_rating,
            AVG(rate_quality) AS avg_quality_rating,
            AVG(qpi_pct) AS avg_quality_performance_index
        FROM master.cr_kpi.kpi_outlet
        GROUP BY rgn, outlet_category
        ORDER BY rgn, avg_customer_satisfaction_service DESC;
    """,

    "q4": """
        SELECT 
            service_outlet,
            rgn,
            outlet_category,
            intake_unit,
            intake_pct,
            revenue_pct,
            eappointment_pct,
            parts_pct,
            lubricant_pct,
            qpi_pct,
            cs_service_pct
        FROM master.cr_kpi.kpi_outlet
        WHERE intake_unit > (SELECT AVG(intake_unit) FROM master.cr_kpi.kpi_outlet)
        ORDER BY intake_unit DESC;
    """,

    "q5": """
        SELECT 
            service_outlet,
            rgn,
            outlet_category,
            cs_service_pct,
            rate_performance,
            rate_quality,
            qpi_pct,
            intake_unit,
            revenue_pct
        FROM master.cr_kpi.kpi_outlet
        WHERE cs_service_pct < 80 -- Focusing on outlets with service CS below 80%
        ORDER BY cs_service_pct ASC;
    """
}