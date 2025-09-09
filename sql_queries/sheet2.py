second_sql_map = {
    "q1": """
        SELECT 
            rgn,
            AVG(new_car_reg_unit) AS avg_new_car_reg,
            AVG(new_car_reg_pct) AS avg_registration_rate,
            AVG(gear_up_ach_pct) AS avg_gear_up_achievement,
            AVG(cs_sales_pct) AS avg_customer_satisfaction_sales,
            AVG(nps_sales_pct) AS avg_nps_sales
        FROM master.cr_kpi.kpi_outlet
        GROUP BY rgn
        ORDER BY avg_new_car_reg DESC;
    """,

    "q2": """
        SELECT 
            outlet_category,
            AVG(new_car_reg_unit) AS avg_new_car_reg,
            AVG(new_car_reg_pct) AS avg_registration_rate,
            AVG(gear_up_ach_pct) AS avg_gear_up_achievement,
            AVG(ins_renew_1st_pct) AS avg_insurance_renewal_first,
            AVG(ins_renew_overall_pct) AS avg_insurance_renewal_overall
        FROM master.cr_kpi.kpi_outlet
        GROUP BY outlet_category
        ORDER BY avg_new_car_reg DESC;
    """,

    "q3": """
        SELECT 
            rgn,
            outlet_category,
            COUNT(*) AS outlet_count,
            AVG(new_car_reg_unit) AS avg_new_car_reg,
            AVG(gear_up_ach_pct) AS avg_gear_up_achievement,
            AVG(ins_renew_1st_pct) AS avg_insurance_renewal_first
        FROM master.cr_kpi.kpi_outlet
        GROUP BY rgn, outlet_category
        ORDER BY rgn, avg_new_car_reg DESC;
    """,

    "q4": """
        SELECT 
            sales_outlet,
            rgn,
            outlet_category,
            new_car_reg_unit,
            new_car_reg_pct,
            gear_up_ach_pct,
            cs_sales_pct,
            nps_sales_pct,
            ins_renew_1st_pct,
            ins_renew_overall_pct,
            pov_pct
        FROM master.cr_kpi.kpi_outlet
        WHERE new_car_reg_unit > (SELECT AVG(new_car_reg_unit) FROM master.cr_kpi.kpi_outlet)
        ORDER BY new_car_reg_unit DESC;
    """
}