# VERSION 1: SALES CENTER PERFORMANCE ANALYSIS

## **SHEET 1: VOLUME (Weekly Registration Volume)**

### **1.1 High-Level Weekly Volume Overview**
```sql
-- Weekly registration volume summary for June 2025
SELECT 
    DATEPART(WEEK, r.registration_date) as week_number,
    DATENAME(WEEK, r.registration_date) as week_start_date,
    COUNT(*) as total_registrations,
    COUNT(DISTINCT r.sales_center_code) as active_outlets,
    COUNT(DISTINCT r.salesman_id) as active_salespeople
FROM REG_VehicleRegistrations r
WHERE r.registration_date >= '2025-06-01' 
    AND r.registration_date < '2025-07-01'
    AND r.registration_date IS NOT NULL
    AND((r.loan_amount_approved is not NULL and r.loan_amount_approved <> 0)  or r.on_the_road_price is not NULL)
GROUP BY DATEPART(WEEK, r.registration_date), DATENAME(WEEK, r.registration_date)
ORDER BY week_number;
```

suggestme7725apassword


### **1.2 Volume by Outlet Category (Primary Drill-Down)**
```sql
-- Weekly volume by outlet category
SELECT 
    DATEPART(WEEK, r.registration_date) as week_number,
    o.outlet_category,
    COUNT(*) as registrations,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY DATEPART(WEEK, r.registration_date)), 2) as market_share_percent
FROM REG_VehicleRegistrations r
JOIN Outlet_Master o ON r.sales_center_code = o.sales_center_code
WHERE r.registration_date >= '2025-06-01' 
    AND r.registration_date < '2025-07-01'
    AND r.registration_date IS NOT NULL
    AND((r.loan_amount_approved is not NULL and r.loan_amount_approved <> 0)  or r.on_the_road_price is not NULL)
GROUP BY DATEPART(WEEK, r.registration_date), o.outlet_category
ORDER BY week_number, outlet_category;
```

### **1.3 Volume by Service Type (Secondary Drill-Down)**
```sql
-- Weekly volume by service type within outlet categories
SELECT 
    DATEPART(WEEK, r.registration_date) as week_number,
    o.outlet_category,
    o.service_type,
    COUNT(*) as registrations,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY DATEPART(WEEK, r.registration_date), o.outlet_category), 2) as category_share_percent
FROM REG_VehicleRegistrations r
JOIN Outlet_Master o ON r.sales_center_code = o.sales_center_code
WHERE r.registration_date >= '2025-06-01' 
    AND r.registration_date < '2025-07-01'
    AND r.registration_date IS NOT NULL
    AND((r.loan_amount_approved is not NULL and r.loan_amount_approved <> 0)  or r.on_the_road_price is not NULL)
GROUP BY DATEPART(WEEK, r.registration_date), o.outlet_category, o.service_type
ORDER BY week_number, outlet_category, service_type;
```

### **1.4 Geographic Distribution (Region → State Drill-Down)**
```sql
-- Volume by region and state
SELECT 
    DATEPART(WEEK, r.registration_date) as week_number,
    o.region,
    o.state,
    COUNT(*) as registrations,
    COUNT(DISTINCT r.sales_center_code) as outlets_active
FROM REG_VehicleRegistrations r
JOIN Outlet_Master o ON r.sales_center_code = o.sales_center_code
WHERE r.registration_date >= '2025-06-01' 
    AND r.registration_date < '2025-07-01'
    AND r.registration_date IS NOT NULL
    AND((r.loan_amount_approved is not NULL and r.loan_amount_approved <> 0)  or r.on_the_road_price is not NULL)
GROUP BY DATEPART(WEEK, r.registration_date), o.region, o.state
ORDER BY week_number, region, state;
```

### **1.5 Customer Segment Volume**
```sql
-- Volume by customer category
SELECT 
    DATEPART(WEEK, r.registration_date) as week_number,
    o.outlet_category,
    r.customer_category,
    COUNT(*) as registrations,
    ROUND(AVG(CAST(r.data_completeness_score AS FLOAT)) * 100, 1) as avg_data_quality_percent
FROM REG_VehicleRegistrations r
JOIN Outlet_Master o ON r.sales_center_code = o.sales_center_code
WHERE r.registration_date >= '2025-06-01' 
    AND r.registration_date < '2025-07-01'
    AND r.registration_date IS NOT NULL
    AND((r.loan_amount_approved is not NULL and r.loan_amount_approved <> 0)  or r.on_the_road_price is not NULL)
GROUP BY DATEPART(WEEK, r.registration_date), o.outlet_category, r.customer_category
ORDER BY week_number, outlet_category, customer_category;
```

## **SHEET 2: EFFICIENCY (Registration Processing Efficiency)**

### **2.1 Overall Processing Efficiency Overview**
```sql
-- Weekly processing efficiency summary
SELECT 
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
    AND((r.loan_amount_approved is not NULL and r.loan_amount_approved <> 0)  or r.on_the_road_price is not NULL)
GROUP BY DATEPART(WEEK, r.registration_date)
ORDER BY week_number;
```

### **2.2 Efficiency by Outlet Category**
```sql
-- Processing efficiency by outlet category
SELECT 
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
    AND((r.loan_amount_approved is not NULL and r.loan_amount_approved <> 0)  or r.on_the_road_price is not NULL)
GROUP BY DATEPART(WEEK, r.registration_date), o.outlet_category
ORDER BY week_number, outlet_category;
```

### **2.3 Efficiency by Service Type**
```sql
-- Processing efficiency by service type (1S/2S/3S comparison)
SELECT 
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
    AND((r.loan_amount_approved is not NULL and r.loan_amount_approved <> 0)  or r.on_the_road_price is not NULL)
GROUP BY DATEPART(WEEK, r.registration_date), o.outlet_category, o.service_type
ORDER BY week_number, outlet_category, service_type;
```

### **2.4 Individual Outlet Performance Ranking**
```sql
-- Top and bottom performing individual outlets by efficiency
SELECT 
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
    AND((r.loan_amount_approved is not NULL and r.loan_amount_approved <> 0)  or r.on_the_road_price is not NULL)
GROUP BY r.sales_center_code, r.sales_center_name, o.outlet_category, o.service_type, o.region, o.state
HAVING COUNT(*) >= 5  -- Only outlets with meaningful volume
ORDER BY o.outlet_category, efficiency_rank_in_category;
```

## **SHEET 3: VALUE (Business Impact & Performance)**

### **3.1 Value Overview by Week**
```sql
-- Weekly business value metrics using unified transaction value
SELECT 
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
ORDER BY week_number;
```

### **3.2 Value Performance by Outlet Category**
```sql
-- Value analysis by outlet category using unified transaction value
SELECT 
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
ORDER BY week_number, outlet_category;
```

### **3.3 High-Performance Outlet Identification**
```sql
-- Outlet performance tiers based on volume, efficiency, and value
WITH outlet_performance AS (
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
    HAVING COUNT(*) >= 3  -- Minimum volume threshold
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
ORDER BY outlet_category, composite_score DESC;
```

### **3.4 Salesperson Productivity Analysis**
```sql
-- Sales team effectiveness within outlet performance context
SELECT 
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
HAVING COUNT(*) >= 5  -- Minimum activity threshold
ORDER BY week_number, outlet_category, registrations DESC;
```


