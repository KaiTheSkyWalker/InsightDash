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
        "- 1S focus KPIs: New Car Reg, Gear Up, Insurance, POV, NPS Sales. \n"
        "- 2S focus KPIs: Intake, Revenue, Parts, Lubricant, NPS Svc, E-Appointment, QPI.\n"
        "- 1+2S/3S use blended metrics from both sides.\n\n"
        "Definition of Quality vs Performance parameters (use this consistently):\n"
        "- Quality parameters: QPI (qpi_pct), E-Appointment (eappointment_pct), NPS Sales (nps_sales_pct), NPS Service (cs_service_pct).\n"
        "- All other KPI % metrics belong to Performance.\n\n"
        "Axis Thresholds by Outlet Type (for interpreting X/Y scatter parameters):\n"
        "- 1S: Threshold X = 35, Threshold Y = 60.\n"
        "- 2S: Threshold X = 40, Threshold Y = 55.\n"
        "- 1+2S: Threshold X = 30, Threshold Y = 50.\n"
        "- 3S: Threshold X = 35, Threshold Y = 60.\n\n"
        "Interpreting % Achievement: 100% = target achieved; >100% = target exceeded; <100% = gap.\n"
        "Some KPIs (e.g., NPS, QPI) are composites or tiered scores; >100% still indicates exceeding the blended target.\n"
    )


def build_role_block() -> str:
    return (
        "Role: You are a strict, quantitative data analyst. Your sole task is to analyze the provided snapshot of CR KPI data.\n"
        "Critical Directive: Your analysis MUST be based exclusively on the provided figures. You MUST NOT infer any time-based trends (e.g., improvement, decline, momentum) as this is a single point in time.\n\n"
        "Non-Negotiable Context: All insights must frame performance through the fundamental trade-off between short-term financial performance (sales, revenue) and long-term customer health (satisfaction, loyalty).\n"
        "**Quantification Mandate: You MUST quantify all claims. Instead of 'low' or 'high', state the actual values, ranges, and percentages. Estimate potential impact (e.g., revenue risk, churn probability) based on the magnitude of quality gaps.**\n\n"
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


def build_thinking_process_block() -> str:
    return (
        "\nTHINKING PROCESS & ANALYTICAL FRAMEWORK:\n"
        "1. DATA-DRIVEN STORY IDENTIFICATION:\n"
        "   - First understand the data structure: What are the key dimensions, metrics, and segments?\n"
        "   - Identify the dominant patterns: What immediately stands out as exceptional (high/low values, distributions)?\n"
        "   - Look for contradictions: Where does the data contradict expected patterns or business assumptions?\n"
        "   - Never assume patterns exist; let the data reveal the true story.\n\n"
        "2. PATTERN ANALYSIS WITH QUANTITATIVE RIGOR:\n"
        "   - For any observed pattern, quantify its magnitude and significance. Use exact values, ranges, and percentages.\n"
        "   - **RISK QUANTIFICATION: For the outlets, estimate the potential business risk. Calculate the gap between their quality score and the threshold. The larger the gap and the group size, the higher the potential revenue loss and customer churn risk.**\n"
        "   - Compare against relevant benchmarks (thresholds, averages, targets).\n"
        "   - Assess pattern consistency across different segments and dimensions.\n"
        "   - Identify whether patterns represent opportunities, risks, or anomalies.\n\n"
        "3. ROOT CAUSE HYPOTHESIS DEVELOPMENT:\n"
        "   - Develop data-supported hypotheses for why patterns exist.\n"
        "   - **CLARITY ON PERFORMANCE: When labeling performance (e.g., 'high'), explicitly name the driving KPI(s) (e.g., 'high car_reg_pct of 150%'). Never use vague terms.**\n"
        "   - Look for correlations between different metrics that might explain observed patterns.\n"
        "   - Consider both performance drivers and potential quality compromises.\n"
        "   - Acknowledge when data is insufficient to determine causality.\n\n"
        "4. ACTIONABLE INSIGHT GENERATION:\n"
        "   - Translate patterns into business implications: What do these patterns mean for short-term results and long-term health?\n"
        "   - **PRIORITIZATION: Rank recommendations by potential impact and urgency. Data integrity issues (e.g., 0 values) are top priority. Then address the largest quality gaps affecting the most outlets.**\n"
        "   - Provide specific, evidence-based recommendations tied directly to the data patterns.\n"
        "   - Clearly distinguish between strategic imperatives and tactical optimizations.\n\n"
        "5. COMMUNICATION PRINCIPLES:\n"
        "   - Lead with the most important finding, supported by quantitative evidence.\n"
        "   - Avoid absolute statements; use probability-based language ('suggests', 'indicates', 'likely').\n"
        "   - Acknowledge data limitations and boundaries of the analysis.\n"
        "   - Connect insights to business outcomes, not just statistical patterns.\n\n"
        "6. QUALITY-PERFORMANCE TRADEOFF ASSESSMENT (SPECIFIC TO CR KPI CONTEXT):\n"
        "   - Always evaluate whether performance achievements come at the expense of quality metrics.\n"
        "   - **DEFINE 'HEALTHY': Describe 'A' outlets as 'sustainable' or 'balanced'. Explicitly state they achieve high performance KPIs (name them, e.g., revenue_pct >100%) WHILE maintaining high quality scores (name them, e.g., cs_service_pct > threshold).**\n"
        "   - Identify where quality investments might be compromising short-term performance.\n"
        "   - Assess the sustainability of current performance-quality balance.\n"
        "   - Recommend adjustments to optimize the performance-quality equilibrium.\n"
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


def build_prompt_individual(
    payload: dict, context_text: str = "", focus_hint: str = ""
) -> str:
    ROLE_BLOCK = build_role_block()
    KB_TEXT = build_kb_text()
    CATEGORY_RULE = build_categorical_analysis_rule()
    DATA_DICTIONARY = build_data_dictionary()
    THINKING_PROCESS = build_thinking_process_block()
    OUTPUT_BLOCK = build_generalized_insight_prompt()

    # Build parameter focus instructions from graph parameters
    parameter_focus_instructions = build_parameter_focus_instructions(
        extract_graph_parameters(payload)
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
        + THINKING_PROCESS
        + parameter_focus_instructions
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
    THINKING_PROCESS = build_thinking_process_block()

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
        + THINKING_PROCESS
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
