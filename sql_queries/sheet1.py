first_sql_map = {
    "q1": """
        SELECT 
            DATEPART(WEEK, r.registration_date) AS week_number,
            DATENAME(WEEK, r.registration_date) AS week_start_date,
            COUNT(*) AS total_registrations,
            COUNT(DISTINCT r.sales_center_code) AS active_outlets,
            COUNT(DISTINCT r.salesman_id) AS active_salespeople
        FROM REG_VehicleRegistrations r
        WHERE r.registration_date >= '2025-06-01' 
          AND r.registration_date < '2025-07-01'
          AND r.registration_date IS NOT NULL
          AND (
              (r.loan_amount_approved IS NOT NULL AND r.loan_amount_approved <> 0)  
               OR r.on_the_road_price IS NOT NULL
          )
        GROUP BY 
            DATEPART(WEEK, r.registration_date),
            DATENAME(WEEK, r.registration_date)
        ORDER BY week_number;
    """,

    "q2": """
        SELECT 
            DATEPART(WEEK, r.registration_date) AS week_number,
            o.outlet_category,
            COUNT(*) AS registrations,
            ROUND(
                COUNT(*) * 100.0 
                / SUM(COUNT(*)) OVER (PARTITION BY DATEPART(WEEK, r.registration_date)),
                2
            ) AS market_share_percent
        FROM REG_VehicleRegistrations r
        JOIN Outlet_Master o ON r.sales_center_code = o.sales_center_code
        WHERE r.registration_date >= '2025-06-01' 
          AND r.registration_date < '2025-07-01'
          AND r.registration_date IS NOT NULL
          AND (
              (r.loan_amount_approved IS NOT NULL AND r.loan_amount_approved <> 0)  
               OR r.on_the_road_price IS NOT NULL
          )
        GROUP BY 
            DATEPART(WEEK, r.registration_date),
            o.outlet_category
        ORDER BY week_number, outlet_category;
    """,

    "q3": """
        SELECT 
            DATEPART(WEEK, r.registration_date) AS week_number,
            o.outlet_category,
            o.service_type,
            COUNT(*) AS registrations,
            ROUND(
                COUNT(*) * 100.0 
                / SUM(COUNT(*)) OVER (
                    PARTITION BY DATEPART(WEEK, r.registration_date), o.outlet_category
                ),
                2
            ) AS category_share_percent
        FROM REG_VehicleRegistrations r
        JOIN Outlet_Master o ON r.sales_center_code = o.sales_center_code
        WHERE r.registration_date >= '2025-06-01' 
          AND r.registration_date < '2025-07-01'
          AND r.registration_date IS NOT NULL
          AND (
              (r.loan_amount_approved IS NOT NULL AND r.loan_amount_approved <> 0)  
               OR r.on_the_road_price IS NOT NULL
          )
        GROUP BY 
            DATEPART(WEEK, r.registration_date),
            o.outlet_category,
            o.service_type
        ORDER BY week_number, outlet_category, service_type;
    """,

    "q4": """
        SELECT 
            DATEPART(WEEK, r.registration_date) AS week_number,
            o.region,
            o.state,
            COUNT(*) AS registrations,
            COUNT(DISTINCT r.sales_center_code) AS outlets_active
        FROM REG_VehicleRegistrations r
        JOIN Outlet_Master o ON r.sales_center_code = o.sales_center_code
        WHERE r.registration_date >= '2025-06-01' 
          AND r.registration_date < '2025-07-01'
          AND r.registration_date IS NOT NULL
          AND (
              (r.loan_amount_approved IS NOT NULL AND r.loan_amount_approved <> 0)  
               OR r.on_the_road_price IS NOT NULL
          )
        GROUP BY 
            DATEPART(WEEK, r.registration_date),
            o.region,
            o.state
        ORDER BY week_number, region, state;
    """,

    "q5": """
        SELECT 
            DATEPART(WEEK, r.registration_date) AS week_number,
            o.outlet_category,
            r.customer_category,
            COUNT(*) AS registrations,
            ROUND(AVG(CAST(r.data_completeness_score AS FLOAT)) * 100, 1) AS avg_data_quality_percent
        FROM REG_VehicleRegistrations r
        JOIN Outlet_Master o ON r.sales_center_code = o.sales_center_code
        WHERE r.registration_date >= '2025-06-01' 
          AND r.registration_date < '2025-07-01'
          AND r.registration_date IS NOT NULL
          AND (
              (r.loan_amount_approved IS NOT NULL AND r.loan_amount_approved <> 0)  
               OR r.on_the_road_price IS NOT NULL
          )
        GROUP BY 
            DATEPART(WEEK, r.registration_date),
            o.outlet_category,
            r.customer_category
        ORDER BY week_number, outlet_category, customer_category;
    """
}
