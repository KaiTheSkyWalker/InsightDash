import json


def build_kb_text() -> str:
    return (
        "KPI CALCULATION FORMULAS:\n"
        "- MTD Actual (%): Month-to-date achievement as percentage of target\n"
        "  * Performance KPIs: MTD Actual / MTD Target * 100\n"
        "  * Insurance: MTD Actual / MTD Target = % (2 Decimal Point)\n"
        "  * NPS: MTD Actual / MTD Target * 100\n"
        "  * QPI: xQPI * (Total claim submission by outlet (Aging ≤3days)/Total claim submission by outlet) * 100\n"
        "- Rate: Points * Achievement (based on MTD Actual %)\n"
        "- Ranking: Sorted based on Rate in Descending order\n\n"
        "Outlet Categories (A/B/C/D) reflect whether an outlet meets performance (quantity) and quality (service) thresholds:\n"
        "- A: Performance > threshold AND Quality > threshold (top performer).\n"
        "- B: Performance > threshold BUT Quality < threshold (good performer but poor service).\n"
        "- C: Performance < threshold BUT Quality > threshold (good service, underperforming).\n"
        "- D: Performance < threshold AND Quality < threshold (poor performer).\n\n"
        "Categorical Hierarchy: A > B > C > D. When comparing categories, treat A as strictly better than B, B better than C, and so on.\n\n"
        "Outlet Types indicate business functions and relevant KPIs: **1S (Sales only)**, **2S (Service only)**, **1+2S/3S (Sales & Service)**.\n"
        "- 1S KPIs: New Car Reg, Gear Up, Insurance, POV, NPS Sales. \n"
        "- 2S KPIs: Intake, Revenue, Parts, Lubricant, NPS Svc, E-Appointment, QPI.\n"
        "- 1+2S/3S use blended metrics from both sides.\n\n"
        "Definition of Quality vs Performance parameters (use this consistently):\n"
        "- Quality parameters: QPI (qpi_pct), E-Appointment (eappointment_pct), NPS Sales (nps_sales_pct), NPS Service (cs_service_pct).\n"
        "- All other KPI % metrics belong to Performance.\n\n"
        "Axis Thresholds by Outlet Type (for interpreting X/Y scatter parameters):\n"
        "### Y is performance , X is quality\n"
        "- 1S: Threshold X = 35, Threshold Y = 60.\n"
        "- 2S: Threshold X = 40, Threshold Y = 55.\n"
        "- 1+2S: Threshold X = 30, Threshold Y = 50.\n"
        "- 3S: Threshold X = 35, Threshold Y = 60.\n\n"
        "Interpreting % Achievement: 100% = target achieved; >100% = target exceeded; <100% = gap.\n"
        "Some KPIs (e.g., NPS, QPI) are composites or tiered scores; >100% still indicates exceeding the blended target.\n"
        "\nOutlet Type KPI Scope Rule:\n"
        "- 1S (Sales-only) focus KPIs: New Car Reg, Gear Up, Insurance, POV, NPS Sales. Treat service KPIs as 0/NA for 1S.\n"
        "- 2S (Service-only) focus KPIs: Intake, Revenue, Parts, Lubricant, NPS Svc, E-Appointment, QPI. Treat sales KPIs as 0/NA for 2S.\n"
        "- 1+2S/3S use blended metrics from both sides; all KPIs apply.\n"
    )


def build_role_block() -> str:
    return (
        "Role: You are a strict, quantitative data analyst. Your sole task is to analyze the provided snapshot of CR KPI data.\n"
        "Critical Directive: Your analysis MUST be based exclusively on the provided figures. You MUST NOT infer any time-based trends (e.g., improvement, decline, momentum) as this is a single point in time.\n\n"
        "Non-Negotiable Context: All insights must frame performance through the fundamental trade-off between short-term financial performance (sales, revenue) and long-term customer health (satisfaction, loyalty).\n"
        "**Quantification Mandate: You MUST quantify all claims. Instead of 'low' or 'high', state the actual values, ranges, and percentages. Estimate potential impact (e.g., revenue risk, churn probability) based on the magnitude of quality gaps.**\n\n"
        "Timeframe Guard: Do NOT mention or assume timeframes (e.g., 'MTD', 'YTD', 'MoM', 'YoY') unless these exact terms appear in the dataset columns or metadata."
        " If absent, treat percentages as timeless normalized achievements and avoid any timeframe terminology.\n\n"
    )


def build_categorical_analysis_rule() -> str:
    return (
        "\nCATEGORICAL ANALYSIS DECISION TREE (USE THIS):\n"
        "- If the largest group is 'A' outlets: The region is healthy. Insight = 'This region successfully balances performance and quality.'\n"
        "- If the largest group is 'B' outlets: The region is at risk. Insight = 'This region is prioritizing short-term sales over customer experience, which threatens long-term loyalty.' This is the most common and critical insight.\n"
        "- If the largest group is 'C' outlets: The region is struggling but has good service. Insight = 'This region has strong customer processes but is failing to achieve sales and volume targets.'\n"
        "- If the largest group is 'D' outlets: The region is in crisis. Insight = 'This region is failing across all key performance and quality indicators.'\n"
        "- Compare A vs. D: Always note the disparity between top and bottom performers.\n"
    )


def build_data_dictionary() -> str:
    return (
        "Data Dictionary & Terminology:\n"
        "KPI Parameters:\n"
        "Performance:\n"
        "- Car Reg (New Car Registration): Number of new vehicles registered (primary sales volume).\n"
        "- Intake (Job Intake): Number of repair orders/service jobs opened (service volume).\n"
        "- Revenue (Service Revenue): Income from repair orders (after-sales).\n"
        "- Parts (Parts Sales): Revenue from spare parts sales.\n"
        "- Lubricant (Lubricant Sales): Quantity or revenue from engine oil/lubricants.\n"
        "- Gear Up (Accessory Sales): Vehicles fitted with optional accessories / accessory revenue.\n"
        "- Ins. T1 (Insurance Tier 1 New): Insurance policies sold for new vehicles.\n"
        "- Ins. Renew O/all (Insurance Renewal Overall): Renewed insurance policies for vehicles of any age.\n"
        "- POV (Trade-In): Perodua vehicles taken as trade-ins for new purchases.\n"
        "Quality:\n"
        "- NPS Sales: Net Promoter Score from sales surveys.\n"
        "- NPS Svc: Net Promoter Score from service surveys.\n"
        "- E-Appt (E-Appointment): Digital service appointments (Booking/Confirmed/No-Show).\n"
        "- QPI (Quality Performance Indicator): % of warranty claims submitted within required timeframe (≤3 days).\n\n"
        "Other Terms:\n"
        "- Outlet Type: 1S (Sales), 2S (Service), 1+2S (Sales & Service), 3S (Sales, Service, Spare Parts).\n"
        "- Outlet Category: Grade A/B/C/D based on Performance & Quality thresholds.\n"
        "- MTD/YTD Actual/Target: Month/Year-to-date achieved vs goal.\n"
        "- Threshold: Minimum acceptable level for Performance/Quality.\n"
        "- Weightage: Relative KPI importance by outlet type.\n"
    )



def build_generalized_insight_prompt() -> str:
    """
    Generates a structured prompt for data analysis that is domain-agnostic.
    """
    return (
        "Provide a structured analysis of the data based on the following format:\n\n"
        "### 1. Observation\n"
        "- State the most significant, factual patterns from the data.\n"
        "- Use short, direct bullet points.\n"
        "- Quantify your findings with precise numbers, ranges, or counts.\n"
        "  - **Example:** 'The [metric_name] for [Segment A] ranges from [X] to [Y].'\n"
        "  - **Example:** '[Number] of entities have a value of 0 for the [metric_name] parameter.'\n\n"
        "- Always state the explicit min and max for each numeric KPI you reference. If grouped statistics by 'outlet_category' or 'outlet_type' are provided, include the per-group min and max for the primary KPI(s).\n\n"
        "### 2. Interpretation\n"
        "- Explain the business or practical implications of your observations.\n"
        "- Identify the key drivers behind the observed patterns and the relationships between metrics.\n"
        "  - **Example:** 'The high performance in [Metric A] for [Segment B] appears to be negatively correlated with [Metric C], suggesting a potential trade-off.'\n"
        "- Quantify the potential impact, risk, or opportunity.\n"
        "  - **Example:** 'The cluster of [Number] entities in [Segment C] shows an average [Metric D] that is [Value/Percentage] below the target, indicating a high risk of [describe the business risk, e.g., user churn, quality failure, revenue loss].'\n\n"
        "### 3. Recommendation\n"
        "- Propose clear, actionable next steps based on your interpretation.\n"
        "- Prioritize your recommendations to guide decision-making.\n"
        "  - **High Priority:** Address critical issues (e.g., data integrity problems, major risks, or opportunities affecting the largest segments).\n"
        "  - **Medium Priority:** Focus on important optimizations or further investigations.\n"
        "  - **Foundation:** Suggest general best practices or foundational improvements.\n"
        "- Each recommendation should be directly linked to a specific, quantified observation.\n"
        "  - **Example:** 'Given that [Number] entities have 0 values for [metric_name], the top priority is to audit the data pipeline to correct this potential anomaly.'\n\n"
        "### Parameter Focus Coverage\n"
        "- Conclude with a brief summary for each key parameter analyzed.\n"
        "- For each parameter, provide a single bullet point with a one-sentence, numeric summary.\n"
        "  - **Example:** '[parameter_name]: The values range from [min] to [max], with the majority of entities clustered around [central_tendency_value].'\n"
        "  - **Example:** '[categorical_parameter]: The most prevalent category is '[Category_X],' accounting for [Percentage]% of the data.'\n"
    )


# You can then call the function to get the prompt string:
# generalized_prompt = build_generalized_insight_prompt()
# print(generalized_prompt)
def extract_graph_parameters(payload: dict) -> list:
    params = []
    seen = set()

    # From top-level metadata
    metadata = payload.get("metadata", {})
    for key in ("x_axis", "y_axis", "legend"):
        val = metadata.get(key)
        if val and val not in seen:
            seen.add(val)
            params.append(val)

    # From charts_meta (handles different chart types)
    for chart in payload.get("charts_meta", []):
        meta = chart.get("meta", {})
        for key in ("x", "y", "color", "value", "size"):
            val = meta.get(key)
            if val and val not in seen:
                seen.add(val)
                params.append(val)

    return params


def build_parameter_focus_instructions(parameters: list) -> str:
    if not parameters:
        return ""

    bullet_lines = "".join([f"- {p}\n" for p in parameters])
    # Tailored requirements for common x/y/legend parameters
    has_quality = "rate_quality" in parameters
    has_performance = "rate_performance" in parameters
    has_category = "outlet_category" in parameters

    details = []
    details.append(
        "Explicit Mention Rule: You MUST explicitly name every parameter above in your output. "
        "Use the exact parameter names verbatim (e.g., 'rate_quality', not a synonym)."
    )
    if has_quality and has_performance:
        details.append(
            "Observation Requirement: Include at least one sentence that jointly discusses 'rate_quality' (X-axis) and 'rate_performance' (Y-axis), "
            "quantifying their relationship using concrete values (e.g., min/max, median, clusters, or correlation direction)."
        )
    if has_category:
        details.append(
            "Legend Requirement: Reference 'outlet_category' explicitly by name and compare category shares (A/B/C/D). "
            "State which category is most prevalent and call out any notable minority group(s)."
        )
    details.append(
        "Checklist Requirement: End your response with a short 'Parameter Focus Coverage' section. "
        "Provide exactly one bullet per parameter listed above, each bullet naming the parameter and giving a one-line numeric summary (e.g., range, extremes, mean, or category counts)."
    )
    details.append(
        "Do not omit any parameter from the list above. If a parameter is genuinely absent from the data, state 'not present' in the coverage section."
    )

    return (
        "\nPARAMETER FOCUS INSTRUCTIONS:\n"
        "Focus your insights on these chart parameters (including legend). All must be covered explicitly:\n"
        f"{bullet_lines}\n" + "\n".join(details) + "\n"
        "Use other columns for additional context only; base primary comparisons and conclusions on the parameters above.\n"
    )


def _format_col_stats(name: str, st: dict) -> str:
    missing = st.get("missing", 0)
    if {"min", "max", "mean"}.issubset(st.keys()):
        return (
            f"- {name}: min={st.get('min')}, p25={st.get('p25')}, median={st.get('median')}, "
            f"p75={st.get('p75')}, max={st.get('max')}, mean={st.get('mean')}, std={st.get('std')} (missing={missing})"
        )
    if "true" in st and "false" in st:
        return f"- {name}: true={st.get('true')}, false={st.get('false')} (missing={missing})"
    if "unique" in st:
        tops = st.get("top") or []
        tops_s = ", ".join(
            f"{t.get('value')}={t.get('count')} ({t.get('pct')}%)" for t in tops
        )
        return f"- {name}: unique={st.get('unique')}, top: {tops_s} (missing={missing})"
    if "min" in st and "max" in st:
        return f"- {name}: min={st.get('min')}, max={st.get('max')} (missing={missing})"
    return f"- {name}: count={st.get('count', 0)} (missing={missing})"


def build_computed_stats_block(payload: dict) -> str:
    lines = []
    charts = payload.get("charts", []) or []
    any_stats = False
    for ch in charts:
        stats = ch.get("computed_stats") or {}
        gstats = ch.get("group_stats") or {}
        if not stats and not gstats:
            continue
        any_stats = True
        title = ch.get("graph_label") or ch.get("graph_id")
        lines.append(f"### Computed Statistics — {title}")
        if stats:
            for col, st in stats.items():
                try:
                    lines.append(_format_col_stats(col, st))
                except Exception:
                    pass
            lines.append("")
        if gstats:
            lines.append("Grouped statistics by dimension:")
            for dim, groups in gstats.items():
                lines.append(f"- By {dim}:")
                for gval, cols in groups.items():
                    lines.append(f"  - {gval}:")
                    for cname, st in cols.items():
                        lines.append(
                            f"    - {cname}: min={st.get('min')}, max={st.get('max')}, range={st.get('range')}, mean={st.get('mean')} (n={st.get('count')})"
                        )
            lines.append("")
        # Include large-table context stats if present (Tab 3 special handling)
        ctx = ch.get("context_stats") or {}
        if ctx:
            big = ctx.get("large_computed_stats") or {}
            bigg = ctx.get("large_group_stats") or {}
            lines.append("Additional context statistics (large table):")
            for col, st in (big.items() if isinstance(big, dict) else []):
                try:
                    lines.append(_format_col_stats(col, st))
                except Exception:
                    pass
            if bigg:
                lines.append("- Grouped (large table):")
                for dim, groups in bigg.items():
                    lines.append(f"  - By {dim}:")
                    for gval, cols in groups.items():
                        lines.append(f"    - {gval}:")
                        for cname, st in cols.items():
                            lines.append(
                                f"      - {cname}: min={st.get('min')}, max={st.get('max')}, range={st.get('range')}, mean={st.get('mean')} (n={st.get('count')})"
                            )
            lines.append("")
    if not any_stats:
        return ""
    header = (
        "\nCOMPUTED STATISTICS (authoritative, precomputed from pandas):\n"
        "Use ONLY the computed statistics below for the 'Observation' section.\n"
        "Do NOT do any arithmetic yourself; treat these as exact facts.\n"
        "MANDATORY: Explicitly state the min and max for each numeric column. If grouped statistics are provided (by 'outlet_category' or 'outlet_type'), include the min and max per group for the primary KPIs you discuss.\n"
        "If both a small and large table are present for a chart (e.g., Tab 3 KPI gaps), FOCUS your Observations on the SMALL table; use the large-table statistics only as supporting context.\n\n"
    )
    return header + "\n".join(lines)


def build_prompt_individual(
    payload: dict, context_text: str = "", focus_hint: str = ""
) -> str:
    ROLE_BLOCK = build_role_block()
    KB_TEXT = build_kb_text()
    CATEGORY_RULE = build_categorical_analysis_rule()
    DATA_DICTIONARY = build_data_dictionary()
    OUTPUT_BLOCK = build_generalized_insight_prompt()

    # Build parameter focus instructions from graph parameters
    parameter_focus_instructions = build_parameter_focus_instructions(
        extract_graph_parameters(payload)
    )

    computed_block = build_computed_stats_block(payload)

    # Month-aware instruction: if any table contains a 'Month' column, require explicit month comparisons
    def _has_month(p: dict) -> bool:
        try:
            cols = p.get("columns") or []
            if any(str(c) == "Month" for c in cols):
                return True
        except Exception:
            pass
        try:
            rows = p.get("rows") or []
            if rows and isinstance(rows, list) and isinstance(rows[0], dict):
                if any("Month" in r for r in rows[:5]):
                    return True
        except Exception:
            pass
        try:
            gs = p.get("group_stats") or {}
            if isinstance(gs, dict) and "Month" in gs:
                return True
        except Exception:
            pass
        try:
            cstats = p.get("context_stats") or {}
            lgs = cstats.get("large_group_stats") if isinstance(cstats, dict) else {}
            if isinstance(lgs, dict) and "Month" in lgs:
                return True
        except Exception:
            pass
        return False

    month_present = False
    try:
        if isinstance(payload, dict) and "charts" in payload:
            for ch in payload.get("charts") or []:
                if isinstance(ch, dict) and (
                    _has_month(ch)
                    or (isinstance(ch.get("filters"), dict) and len(ch["filters"].get("months", [])) > 1)
                ):
                    month_present = True
                    break
        else:
            month_present = _has_month(payload) or (
                isinstance(payload.get("filters"), dict)
                and len(payload["filters"].get("months", [])) > 1
            )
    except Exception:
        month_present = False

    MONTH_DIRECTIVE = (
        "\nMONTH-AWARE DIRECTIVE:\n"
        "If a 'Month' column is present, you MUST compare months explicitly.\n"
        "- Quantify month-over-month deltas for the key KPIs you discuss (state sign and magnitude).\n"
        "- Identify where performance improved or declined the most by outlet_category/region/outlet_type as applicable.\n"
        "- Use only the provided computed statistics and grouped stats by 'Month' (if present) to support claims.\n"
        "- Keep comparisons concise and prioritized; avoid repeating trivial differences.\n"
        if month_present
        else ""
    )

    return (
        ROLE_BLOCK
        + "You are a senior data analyst presenting to business stakeholders. I will provide a chart dataset as JSON.\n"
        "Return plain markdown only (no code fences, no introductory text). Be specific, quantified, and evidence-led.\n"
        "Do not be vague or ambiguous: avoid generic statements; support each key claim with concrete numbers, names, and explicit comparisons from the provided data.\n"
        + focus_hint
        + "\nKNOWLEDGE BASE:\n"
        + KB_TEXT
        + CATEGORY_RULE
        + "\nDATA DICTIONARY:\n"
        + DATA_DICTIONARY
        + (f"\nContext/Purpose: {context_text}\n" if context_text else "")
        + parameter_focus_instructions
        + computed_block
        + MONTH_DIRECTIVE
        + OUTPUT_BLOCK
        + "JSON follows:\n```json\n"
        + json.dumps(payload, ensure_ascii=False)
        + "\n```"
    )


def build_prompt_combined(
    payload: dict, context_text: str = "", focus_hint: str = ""
) -> str:
    ROLE_BLOCK = build_role_block()
    KB_TEXT = build_kb_text()
    CATEGORY_RULE = build_categorical_analysis_rule()
    DATA_DICTIONARY = build_data_dictionary()

    # Build parameter focus instructions across all included charts
    parameter_focus_instructions = build_parameter_focus_instructions(
        extract_graph_parameters(payload)
    )

    return (
        ROLE_BLOCK
        + "You are a senior data analyst presenting an integrated insights report to leadership. I will provide datasets for multiple charts as JSON.\n"
        "Return plain markdown only (no code fences). Synthesize across all charts to create a unified, evidence-led narrative.\n"
        "Do not be vague or ambiguous: avoid generic statements; support each key claim with concrete numbers, names, and explicit comparisons from the provided data.\n"
        + focus_hint
        + "\nKNOWLEDGE BASE:\n"
        + KB_TEXT
        + CATEGORY_RULE
        + "\nDATA DICTIONARY:\n"
        + DATA_DICTIONARY
        + (f"\nContext/Purpose: {context_text}\n" if context_text else "")
        + parameter_focus_instructions
        + "Structure your integrated report as follows:\n"
        "\n"
        "## Executive Summary: The Core Narrative\n"
        "- A 2-3 sentence summary synthesizing the most important overarching story across all data. State the key takeaway and its business impact, supported by the top-level magnitude.\n"
        "\n"
        "## Integrated Insights & Relationships (with numbers)\n"
        "- Primary Correlation: Identify the strongest relationship or pattern between the different charts. Support with concrete values and explain why.\n"
        "- Consistent Themes: Detail 2-3 themes that appear across multiple datasets.\n"
        "- Notable Exception/Outlier: Highlight any major outlier or exception to the overall trends that requires investigation.\n"
        "- Hypothesized Drivers: Provide 1–2 hypotheses with justifications that name the exact data points supporting it.\n"
        "\n"
        "## Strategic Implications & Risks\n"
        "- What do these synthesized insights imply for the business?\n"
        "- What is the biggest risk or opportunity if these cross-channel trends continue?\n"
        "\n"
        "## Top Data Evidence\n"
        "- A concise list of the 5-8 most critical data points from across all charts that form the foundation of your analysis.\n"
        "\n"
        "## Recommended Strategic Actions (with Reasons)\n"
        "- Priority Initiative: One primary, cross-functional recommendation that addresses the core narrative.\n"
        "- Focus Area: A specific area for deeper analysis or a targeted program based on the insights.\n"
        "\n"
        "JSON data follows:\n```json\n"
        + json.dumps(payload, ensure_ascii=False)
        + "\n```"
    )
