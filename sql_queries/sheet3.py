third_sql_map = {
    "q1": """SELECT 
    DATEPART(WEEK, r.registration_date) as week_number,
    COUNT(*) as total_registrations,
    COUNT(CASE WHEN (r.on_the_road_price IS NOT NULL OR r.loan_amount_approved IS NOT NULL) THEN 1 END) as registrations_with_value,
    AVG(CASE 
        WHEN r.on_the_road_price IS NOT NULL THEN r.on_the_road_price  
        WHEN r.loan_amount_approved IS NOT NULL THEN r.loan_amount_approved / 0.8  
        ELSE NULL 
    END) as avg_vehicle_value,
    SUM(CASE 
        WHEN r.on_the_road_price IS NOT NULL THEN r.on_the_road_price  
        WHEN r.loan_amount_approved IS NOT NULL THEN r.loan_amount_approved / 0.8  
        ELSE NULL 
    END) as total_sales_value,
    MIN(CASE 
        WHEN r.on_the_road_price IS NOT NULL THEN r.on_the_road_price  
        WHEN r.loan_amount_approved IS NOT NULL THEN r.loan_amount_approved / 0.8  
        ELSE NULL 
    END) as min_value,
    MAX(CASE 
        WHEN r.on_the_road_price IS NOT NULL THEN r.on_the_road_price  
        WHEN r.loan_amount_approved IS NOT NULL THEN r.loan_amount_approved / 0.8  
        ELSE NULL 
    END) as max_value
FROM REG_VehicleRegistrations r
WHERE r.registration_date >= '2025-06-01' 
    AND r.registration_date < '2025-07-01'
    AND r.registration_date IS NOT NULL
    AND((r.loan_amount_approved is not NULL and r.loan_amount_approved <> 0)  or r.on_the_road_price is not NULL)
GROUP BY DATEPART(WEEK, r.registration_date)
ORDER BY week_number;""",
    
    "q2": """SELECT 
    DATEPART(WEEK, r.registration_date) as week_number,
    o.outlet_category,
    COUNT(*) as registrations,
    COUNT(CASE WHEN (r.on_the_road_price IS NOT NULL OR r.loan_amount_approved IS NOT NULL) THEN 1 END) as registrations_with_value,
    AVG(CASE 
        WHEN r.on_the_road_price IS NOT NULL THEN r.on_the_road_price  
        WHEN r.loan_amount_approved IS NOT NULL THEN r.loan_amount_approved / 0.8  
        ELSE NULL 
    END) as avg_vehicle_value,
    SUM(CASE 
        WHEN r.on_the_road_price IS NOT NULL THEN r.on_the_road_price  
        WHEN r.loan_amount_approved IS NOT NULL THEN r.loan_amount_approved / 0.8  
        ELSE NULL 
    END) as total_sales_value,
    ROUND(AVG(CASE 
        WHEN r.on_the_road_price IS NOT NULL THEN r.on_the_road_price  
        WHEN r.loan_amount_approved IS NOT NULL THEN r.loan_amount_approved / 0.8  
        ELSE NULL 
    END) / NULLIF(AVG(CAST(r.days_booking_to_registration AS FLOAT)), 0), 2) as value_per_processing_day
FROM REG_VehicleRegistrations r
JOIN Outlet_Master o ON r.sales_center_code = o.sales_center_code
WHERE r.registration_date >= '2025-06-01' 
    AND r.registration_date < '2025-07-01'
    AND r.registration_date IS NOT NULL
    AND((r.loan_amount_approved is not NULL and r.loan_amount_approved <> 0)  or r.on_the_road_price is not NULL)
GROUP BY DATEPART(WEEK, r.registration_date), o.outlet_category
ORDER BY week_number, outlet_category;""",
    
    "q3": """WITH outlet_performance AS (
    SELECT 
        r.sales_center_code,
        r.sales_center_name,
        o.outlet_category,
        o.service_type,
        o.region,
        COUNT(*) as total_registrations,
        AVG(CAST(r.days_booking_to_registration AS FLOAT)) as avg_processing_days,
        AVG(CASE 
            WHEN r.on_the_road_price IS NOT NULL THEN r.on_the_road_price  
            WHEN r.loan_amount_approved IS NOT NULL THEN r.loan_amount_approved / 0.8  
            ELSE NULL 
        END) as avg_vehicle_value,
        SUM(CASE 
            WHEN r.on_the_road_price IS NOT NULL THEN r.on_the_road_price  
            WHEN r.loan_amount_approved IS NOT NULL THEN r.loan_amount_approved / 0.8  
            ELSE NULL 
        END) as total_sales_value,
        ROUND(COUNT(CASE WHEN r.registration_efficiency = 'Fast' THEN 1 END) * 100.0 / COUNT(*), 2) as fast_processing_rate
    FROM REG_VehicleRegistrations r
    JOIN Outlet_Master o ON r.sales_center_code = o.sales_center_code
    WHERE r.registration_date >= '2025-06-01' 
        AND r.registration_date < '2025-07-01'
        AND r.registration_date IS NOT NULL
        AND r.days_booking_to_registration IS NOT NULL
        AND((r.loan_amount_approved is not NULL and r.loan_amount_approved <> 0)  or r.on_the_road_price is not NULL)
    GROUP BY r.sales_center_code, r.sales_center_name, o.outlet_category, o.service_type, o.region
    HAVING COUNT(*) >= 3
)
SELECT 
    *,
    CASE 
        WHEN total_registrations >= 20 AND fast_processing_rate >= 70 AND avg_vehicle_value >= 50000 THEN 'HIGH_PERFORMER'
        WHEN total_registrations >= 10 AND fast_processing_rate >= 50 AND avg_vehicle_value >= 40000 THEN 'GOOD_PERFORMER' 
        WHEN total_registrations >= 5 AND fast_processing_rate >= 30 THEN 'AVERAGE_PERFORMER'
        ELSE 'NEEDS_IMPROVEMENT'
    END as performance_tier,
    ROUND((total_registrations * 0.3 + fast_processing_rate * 0.4 + COALESCE(avg_vehicle_value/1000, 0) * 0.3), 2) as composite_score
FROM outlet_performance
ORDER BY outlet_category, composite_score DESC;""",
    
    "q4": """SELECT 
    DATEPART(WEEK, r.registration_date) as week_number,
    o.outlet_category,
    r.salesman_id,
    r.salesman_name,
    r.sales_center_code,
    COUNT(*) as registrations,
    AVG(CAST(r.days_booking_to_registration AS FLOAT)) as avg_processing_days,
    AVG(CASE 
        WHEN r.on_the_road_price IS NOT NULL THEN r.on_the_road_price  
        WHEN r.loan_amount_approved IS NOT NULL THEN r.loan_amount_approved / 0.8  
        ELSE NULL 
    END) as avg_deal_value,
    COUNT(DISTINCT r.customer_category) as customer_segment_diversity,
    ROUND(COUNT(*) * 1.0 / COUNT(DISTINCT DATEPART(DAY, r.registration_date)), 2) as daily_registration_rate
FROM REG_VehicleRegistrations r
JOIN Outlet_Master o ON r.sales_center_code = o.sales_center_code
WHERE r.registration_date >= '2025-06-01' 
    AND r.registration_date < '2025-07-01'
    AND r.registration_date IS NOT NULL
    AND r.salesman_id IS NOT NULL
    AND((r.loan_amount_approved is not NULL and r.loan_amount_approved <> 0)  or r.on_the_road_price is not NULL)
GROUP BY DATEPART(WEEK, r.registration_date), o.outlet_category, r.salesman_id, r.salesman_name, r.sales_center_code
HAVING COUNT(*) >= 5
ORDER BY week_number, outlet_category, registrations DESC;"""
}