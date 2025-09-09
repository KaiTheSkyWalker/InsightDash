first_sql_map = {
    "q1": """
        SELECT 
            rgn,
            COUNT(*) AS total_outlets,
            AVG(total_score) AS avg_total_score,
            AVG(rank_nationwide) AS avg_national_rank,
            AVG(rank_region) AS avg_regional_rank
        FROM master.cr_kpi.kpi_outlet
        GROUP BY rgn
        ORDER BY avg_total_score DESC;
    """,

    "q2": """
        SELECT 
            outlet_category,
            COUNT(*) AS outlets_in_category,
            AVG(total_score) AS avg_total_score,
            AVG(new_car_reg_unit) AS avg_new_car_reg,
            AVG(intake_unit) AS avg_intake_units,
            AVG(revenue_pct) AS avg_revenue_performance
        FROM master.cr_kpi.kpi_outlet
        GROUP BY outlet_category
        ORDER BY avg_total_score DESC;
    """,

    "q3": """
        SELECT 
            rgn,
            outlet_category,
            COUNT(*) AS outlet_count,
            AVG(total_score) AS avg_total_score,
            AVG(rank_nationwide) AS avg_national_rank,
            AVG(rank_region) AS avg_regional_rank
        FROM master.cr_kpi.kpi_outlet
        GROUP BY rgn, outlet_category
        ORDER BY rgn, avg_total_score DESC;
    """,

    "q4": """
        SELECT TOP 20
            sales_outlet,
            rgn,
            outlet_category,
            total_score,
            rank_nationwide,
            rank_region,
            new_car_reg_unit,
            intake_unit,
            revenue_pct
        FROM master.cr_kpi.kpi_outlet
        ORDER BY total_score DESC;
    """,

    "q5": """
        SELECT TOP 20
            sales_outlet,
            rgn,
            outlet_category,
            total_score,
            rank_nationwide,
            rank_region,
            new_car_reg_unit,
            intake_unit,
            revenue_pct
        FROM master.cr_kpi.kpi_outlet
        ORDER BY total_score ASC;
    """
}