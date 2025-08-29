second_sql_map = {
    "q1": """SELECT 
    DATEPART(WEEK, r.registration_date) as week_number,
    COUNT(*) as total_registrations,
    AVG(CAST(r.days_booking_to_registration AS FLOAT)) as avg_processing_days,
    COUNT(CASE WHEN r.registration_efficiency = 'Fast' THEN 1 END) as fast_registrations,
    COUNT(CASE WHEN r.registration_efficiency = 'Slow' THEN 1 END) as slow_registrations,
    ROUND(COUNT(CASE WHEN r.registration_efficiency = 'Fast' THEN 1 END) * 100.0 / COUNT(*), 2) as fast_processing_rate_percent
FROM REG_VehicleRegistrations r
WHERE r.registration_date >= '2025-06-01' 
    AND r.registration_date < '2025-07-01'
    AND r.registration_date IS NOT NULL
    AND r.days_booking_to_registration IS NOT NULL
    AND ((r.loan_amount_approved IS NOT NULL AND r.loan_amount_approved <> 0) OR r.on_the_road_price IS NOT NULL)
GROUP BY DATEPART(WEEK, r.registration_date)
ORDER BY week_number;""",
    
    "q2": """SELECT 
    DATEPART(WEEK, r.registration_date) as week_number,
    o.outlet_category,
    COUNT(*) as registrations,
    AVG(CAST(r.days_booking_to_registration AS FLOAT)) as avg_processing_days,
    ROUND(COUNT(CASE WHEN r.registration_efficiency = 'Fast' THEN 1 END) * 100.0 / COUNT(*), 2) as fast_processing_rate_percent,
    MIN(r.days_booking_to_registration) as fastest_processing,
    MAX(r.days_booking_to_registration) as slowest_processing
FROM REG_VehicleRegistrations r
JOIN Outlet_Master o ON r.sales_center_code = o.sales_center_code
WHERE r.registration_date >= '2025-06-01' 
    AND r.registration_date < '2025-07-01'
    AND r.registration_date IS NOT NULL
    AND r.days_booking_to_registration IS NOT NULL
    AND ((r.loan_amount_approved IS NOT NULL AND r.loan_amount_approved <> 0) OR r.on_the_road_price IS NOT NULL)
GROUP BY DATEPART(WEEK, r.registration_date), o.outlet_category
ORDER BY week_number, outlet_category;""",
    
    "q3": """SELECT 
    DATEPART(WEEK, r.registration_date) as week_number,
    o.outlet_category,
    o.service_type,
    COUNT(*) as registrations,
    AVG(CAST(r.days_booking_to_registration AS FLOAT)) as avg_processing_days,
    ROUND(COUNT(CASE WHEN r.registration_efficiency = 'Fast' THEN 1 END) * 100.0 / COUNT(*), 2) as fast_processing_rate_percent,
    ROUND(AVG(CAST(r.data_completeness_score AS FLOAT)) * 100, 1) as avg_data_completeness_percent
FROM REG_VehicleRegistrations r
JOIN Outlet_Master o ON r.sales_center_code = o.sales_center_code
WHERE r.registration_date >= '2025-06-01' 
    AND r.registration_date < '2025-07-01'
    AND r.registration_date IS NOT NULL
    AND r.days_booking_to_registration IS NOT NULL
    AND ((r.loan_amount_approved IS NOT NULL AND r.loan_amount_approved <> 0) OR r.on_the_road_price IS NOT NULL)
GROUP BY DATEPART(WEEK, r.registration_date), o.outlet_category, o.service_type
ORDER BY week_number, outlet_category, service_type;""",
    
    "q4": """SELECT 
    r.sales_center_code,
    r.sales_center_name,
    o.outlet_category,
    o.service_type,
    o.region,
    o.state,
    COUNT(*) as total_registrations,
    AVG(CAST(r.days_booking_to_registration AS FLOAT)) as avg_processing_days,
    ROUND(COUNT(CASE WHEN r.registration_efficiency = 'Fast' THEN 1 END) * 100.0 / COUNT(*), 2) as fast_processing_rate_percent,
    ROW_NUMBER() OVER (PARTITION BY o.outlet_category ORDER BY AVG(CAST(r.days_booking_to_registration AS FLOAT))) as efficiency_rank_in_category
FROM REG_VehicleRegistrations r
JOIN Outlet_Master o ON r.sales_center_code = o.sales_center_code
WHERE r.registration_date >= '2025-06-01' 
    AND r.registration_date < '2025-07-01'
    AND r.registration_date IS NOT NULL
    AND r.days_booking_to_registration IS NOT NULL
    AND ((r.loan_amount_approved IS NOT NULL AND r.loan_amount_approved <> 0) OR r.on_the_road_price IS NOT NULL)
GROUP BY r.sales_center_code, r.sales_center_name, o.outlet_category, o.service_type, o.region, o.state
HAVING COUNT(*) >= 5
ORDER BY o.outlet_category, efficiency_rank_in_category;"""
}