# Dashboard Storylines, Filters, and Interaction Design

This document explains the narrative (story lines) behind each dashboard tab, how cross‑filtering works between the visuals, and why the selected parameters filter the corresponding parameters.

## 1) Story Lines per Tab

### Tab 1 — KPI Overview
Purpose: Establish a high‑level view of outlet performance by region and category, then spotlight top/bottom outlets.

- Regional Performance (Avg Score): Benchmarks each `rgn` by `avg_total_score`. Story: Which regions lead or lag overall?
- Outlet Category Averages: Compares category‑level `avg_total_score` and commercial performance (`avg_revenue_performance`). Story: Which categories are structurally stronger?
- Region × Category Heatmap: `rgn` by `outlet_category` on `avg_total_score`. Story: Where are strong/weak combinations concentrated?
- Top 20 Outlets by Score: Highlights best performers (`total_score`). Story: Who sets the standard?
- Bottom 20 Outlets by Score: Highlights improvement opportunities. Story: Who needs attention/support?

### Tab 2 — Operational Insights (Efficiency)
Purpose: Diagnose processing efficiency across regions and categories and link volume to customer outcomes.

- Regional Efficiency Metrics: Grouped bars for `avg_new_car_reg`, `avg_registration_rate`, `avg_gear_up_achievement`, `avg_customer_satisfaction_sales`, `avg_nps_sales`. Story: Which regions convert faster/better?
- Category Efficiency Metrics: Same lens by `outlet_category`. Story: Which outlet types are operationally consistent?
- Region × Category Heatmap (Avg New Car Reg): Story: Where throughput is strongest/weakest.
- Top Outlets by New Car Reg: High‑volume individual outlets. Story: Who is driving the throughput?
- Registration% vs NPS (size by units): Links conversion to satisfaction. Story: Are we trading speed for satisfaction?

### Tab 3 — Performance Analyzer (Value & Quality)
Purpose: Connect operational volume to business value and quality.

- Regional Value & Ops Metrics: `avg_intake_units`, `avg_intake_percentage`, `avg_revenue_performance`, `avg_parts_performance`, `avg_lubricant_performance`. Story: Which regions deliver business value sustainably?
- Category Value & Ops Metrics: Same lens by `outlet_category`. Story: Which categories monetize best?
- Region × Category Heatmap (Quality Index): `avg_quality_performance_index` (fallback to `avg_customer_satisfaction_service`). Story: Where is service quality reliable?
- Top Service Outlets by Intake Units: Who handles the most service flow?
- Service CS% vs QPI% (size by intake): Relationship between satisfaction and quality. Story: Are high‑volume centers maintaining quality & CS?

## 2) Why Graph Filters What Graph

Cross‑filters follow a “from context → detail” rule: clicking a visual that is authoritative for a dimension (region/category) sets that dimension globally so that all other visuals update consistently. Outlet‑level charts do not push global filters to avoid overfitting the entire dashboard to a single center.

- Tab 1
  - Regional bar → sets `regions`. Rationale: region is the key slice for all other views.
  - Category bars → set `outlet_categories`. Rationale: compare all metrics within the chosen category.
  - Heatmap cell (`rgn`×`outlet_category`) → sets both `regions` and `outlet_categories`. Rationale: lock context to the exact segment.
  - Top/Bottom outlets (barh) → set both via customdata `[rgn, outlet_category]`. Rationale: explore the segment of that outlet.

- Tab 2
  - Regional efficiency bars → set `regions`. Rationale: focus on an under/over‑performing region across all metrics.
  - Category efficiency bars → set `outlet_categories`. Rationale: compare peers within that outlet type.
  - Heatmap (`rgn`×`outlet_category`) → sets both. Rationale: narrow to an exact segment.
  - Top outlets by new car reg → sets `outlet_categories` from the bar’s category. Rationale: explore that category ecosystem.
  - Reg% vs NPS scatter → sets both from customdata `[rgn, outlet_category]`. Rationale: keep the contextual segment.

- Tab 3
  - Regional value bars → set `regions`. Rationale: region is a stable roll‑up.
  - Category value bars → set `outlet_categories`. Rationale: category aggregates shape downstream charts.
  - Heatmap (`rgn`×`outlet_category`) → sets both. Rationale: analyze the exact intersection.
  - Outlet‑level charts (Top Service Outlets; CS% vs QPI%) → do not update global filters (only local center filter). Rationale: avoid forcing all tabs to a single outlet.

This mapping keeps interactions predictable: high‑level slice selectors (region/category) are propagated globally; micros (outlets) stay local.

## 3) Why These Parameters Filter These Parameters

Global filters (all dropdowns):

- Outlet Category (multi): Applies wherever `outlet_category` exists (Tabs 1–3). Rationale: Category normalizes structural differences between outlet types and is a core grouping in the SQL.
- Region (multi): Applies wherever `rgn` exists (Tabs 1–3). Rationale: Region is a leadership/operating unit dimension across all KPIs.
- Score Band (single: All, ≥80, 60–79, <60):
  - Applies to score columns when present: `avg_total_score` (aggregates) and `total_score` (outlets) on Tab 1. Rationale: Quickly narrow to excellence, solid performers, or risk segments without specifying exact ranges.
- Units Band (single: All, ≥50, 20–49, <20):
  - Applies to unit columns where relevant: `avg_new_car_reg`, `avg_intake_units`, `new_car_reg_unit`, `intake_unit` across Tabs 1–3 when present. Rationale: Focus the analysis on scale (high‑volume vs niche) to separate throughput effects from rate metrics.

Design rationale:
- The new database delivers primarily regional/category aggregates plus outlet lists; time is not the central key here. Region and Category are the consistent axes across sheets, while Score and Units provide fast scenario filtering without numeric sliders.
- Numeric bands avoid confusion across different KPIs and keep the global filters compact and performant.

## Interaction Examples

- Click a region bar in Tab 1 → all tabs update to that `rgn`. Heatmaps and rankings now reflect that region only.
- Click a category bar in Tab 2 → all tabs focus on that `outlet_category`; investigate value/quality for just that category in Tab 3.
- Select Score Band ≥80 → Tab 1 shows only top regional/category segments and outlets; Tabs 2–3 remain filtered by Region/Category as set.
- Select Units Band 20–49 → narrows analysis to moderate‑volume segments where rate metrics are often more comparable.

## Notes

- When a chart’s dataset is empty after filtering, the figure remains visible with a title so the layout never collapses.
- Outlet‑level selections on Tab 3 affect only Tab 3 local filters to avoid globally over‑constraining analysis to a single center.
- All cross‑filters are toggleable: clicking the same point again clears the selection.

