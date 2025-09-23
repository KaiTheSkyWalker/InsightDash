def build_second_sql_map(table_name: str) -> dict[str, str]:
    t = f"master.cr_kpi.{table_name}"
    return {
        "dynamic-scatter-plot": f"""
SELECT
    sales_outlet,
    rgn,
    outlet_category,
    outlet_type,
    -- Performance Parameters
    new_car_reg_pct,
    gear_up_ach_pct,
    ins_renew_1st_pct,
    ins_renew_overall_pct,
    pov_pct,
    intake_pct,
    revenue_pct,
    parts_pct,
    lubricant_pct,
    -- Quality Parameters
    cs_sales_pct,
    nps_sales_pct,
    eappointment_pct,
    qpi_pct,
    cs_service_pct
FROM {t}
WHERE new_car_reg_pct IS NOT NULL
   OR gear_up_ach_pct IS NOT NULL
   OR cs_sales_pct IS NOT NULL
   OR nps_sales_pct IS NOT NULL;
"""
    }
