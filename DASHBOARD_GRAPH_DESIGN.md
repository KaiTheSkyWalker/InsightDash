# Dashboard Graph Design & Cross‑Filtering Guide

This document explains the intent and usage of every graph in the dashboard, why each visualization was chosen, and how cross‑filtering works between graphs. It is organized by tab. For each graph you’ll find:

- What the figure represents
- Why this figure is appropriate
- Which parameter(s) it writes when you click (cross‑filter)
- Why those parameter(s) and why it cross‑filters specific other graphs

Throughout the app, colors are consistent:
- Outlet categories share a stable palette across tabs.
- Regions share a stable palette where applicable.
- Performance tiers use: HIGH_PERFORMER (green), GOOD_PERFORMER (blue), AVERAGE_PERFORMER (amber), NEEDS_IMPROVEMENT (red).

Selected charts in the sidebar use the same names as the graph titles for clarity and consistency.

---

## Tab 1 — Overview

This tab provides a high‑level “what happened” view during the selected period with quick cross‑filters.

### 1) Weekly Registration Overview (Line)
- Represents: Total registrations per week.
- Why: A line emphasizes temporal trends and inflection points week‑over‑week.
- Cross‑filter parameter: `week_number`.
- Why this cross‑filter: Week is a unifying time dimension across all datasets, so applying it refines every other chart to the same time slice.

### 2) Outlet Category Market Share (Stacked Bar)
- Represents: Each category’s share (%) per week.
- Why: Stacked bars best communicate parts‑of‑a‑whole per time bucket.
- Cross‑filter parameter: `outlet_category` (and optionally `week_number` via the x‑axis).
- Why this cross‑filter: Category is a primary segmentation across multiple datasets (q2, q3, q5), so filtering by category reveals its composition and footprint elsewhere.

### 3) Service Type Breakdown (Grouped Bar, log Y)
- Represents: Registrations by `service_type`, colored by `outlet_category`.
- Why: Grouped bars compare categories within each service type. Log scale preserves visibility across wide ranges.
- Cross‑filter parameter: `service_type` and/or `outlet_category`.
- Why this cross‑filter: Service type is a key operational lever; filtering by it reveals downstream impacts on volume and category composition.

### 4) Regional Registration Distribution (Stacked Bar, log Y)
- Represents: Registrations by `state`, stacked by `region`.
- Why: Shows geographic distribution and concentration quickly, with log scale for broad ranges.
- Cross‑filter parameter: `region` or `state`.
- Why this cross‑filter: Geography ties to network coverage and performance; applying it sharpens comparisons elsewhere.

### 5) Customer Category Registrations (Grouped Bar, log Y)
- Represents: Registrations by `customer_category`, colored by `outlet_category`.
- Why: Grouped bars compare categories across customer segments; log scale keeps small/large values visible.
- Cross‑filter parameter: `customer_category` and/or `outlet_category`.
- Why this cross‑filter: Customer mix affects both demand and process quality; filtering helps isolate effects by cohort.

Cross‑filter map (Tab 1):
- Sources: All five charts can write filters for week, outlet category, service type, region/state, customer category.
- Targets: All other Tab 1 charts (and Tab 2) consume those filters so the story stays synchronized.

---

## Tab 2 — Operational Insights

This tab dives into processing efficiency and mix, helping explain “how” results were achieved.

### 1) Weekly Trends (Bar + Dual Lines)
- Represents: Weekly total registrations (bar), average processing days (line), fast‑processing rate % (dashed line).
- Why: Combined view shows throughput and speed together; dual axes avoid scaling conflicts.
- Cross‑filter parameter: `week_number`.
- Why cross‑filter: Time decomposition is central to understanding operational change and is applied to all other Tab 2 charts.

### 2) Outlet Category Performance by Week (Grouped Bar)
- Represents: Registrations by `outlet_category` per week.
- Why: Grouped bars clarify category comparisons within each week.
- Cross‑filter parameter: `outlet_category` (and optionally `week_number`).
- Why cross‑filter: Category explains mix shifts seen in Weekly Trends; filtering isolates each category’s behavior.

### 3) Category × Service Type (Heatmap)
- Represents: A matrix of categories vs service types, colored by the chosen metric (registrations or quality/efficiency proxy if available).
- Why: Heatmaps surface hot/cold spots and outliers across two categorical dimensions succinctly.
- Cross‑filter parameter: `outlet_category` and/or `service_type`.
- Why cross‑filter: Lets you spotlight intersections that drive spikes or bottlenecks elsewhere.

### 4) Efficiency Ranking (Top N) (Horizontal Bar)
- Represents: Centers (or best available label) ranked by an efficiency metric (fast rate, avg days, or registrations fallback).
- Why: Ranking quickly identifies leaders/laggards to prioritize actions.
- Cross‑filter parameter: Often `outlet_category` (when present) or center label; used to refine other views.
- Why cross‑filter: Drilling into top/bottom performers should propagate to trend and mix charts to validate hypotheses.

### 5) Regional / State Distribution (Bar)
- Represents: Volume distribution by region/state.
- Why: Bar charts reveal geographic concentration and tail.
- Cross‑filter parameter: `region` or `state`.
- Why cross‑filter: Geography relates to network structure and demand; filter to see its effect on mix and efficiency.

Cross‑filter map (Tab 2):
- Sources: Weekly Trends (week), Category by Week (category, week), Heatmap (category/service type), Efficiency Ranking (center/category), Regional Distribution (region/state).
- Targets: All Tab 2 charts read these filters; Tab 1 charts also respect week/category/region filters for continuity.

---

## Tab 3 — Performance Analyzer

This tab turns the operational data into a compare‑and‑rank lens to find what’s working and where to act.

### 1) Weekly Performance Overview (Grouped Bars)
- Represents: Registrations by `outlet_category` per week.
- Why: A clean “race by week” makes cross‑category momentum obvious.
- Cross‑filter parameter: `week_number`, `outlet_category`.
- Why cross‑filter: These are the core time/mix dimensions; applying them focuses the rest of this tab.

### 2) Efficiency & Value Quadrant (Bubble Scatter)
- Represents: x = avg processing days, y = avg vehicle value, size = registrations, color = `outlet_category`.
- Why: Quadrants split categories into intuitive profiles (fast/high‑value vs slow/low‑value, etc.).
- Cross‑filter parameter: `outlet_category`.
- Why cross‑filter: Category focus here should carry to rankings and tiers to test if positioning is consistent.

### 3) Performance Tier Contribution (100% Stacked Bar)
- Represents: Proportional contribution of tiers (HIGH/GOOD/AVERAGE/NEEDS_IMPROVEMENT) to total sales value and total registrations.
- Why: A normalized view answers “who contributes what share” independent of absolute totals.
- Cross‑filter parameter: `performance_tier`.
- Why cross‑filter: Tier focus should re‑cut the overview, quadrant, and top performers to validate systemic strengths/weaknesses.

### 4) Top Performers (Horizontal Bar)
- Represents: Top centers by `composite_score` (color = tier).
- Why: A clear, sortable leaderboard to action on recognition, coaching, and best‑practice sharing.
- Cross‑filter parameter: `sales_center_code`.
- Why cross‑filter: Selecting a center should propagate to context charts (overview/quadrant/tier) to inspect its neighborhood.

### 5) Center Performance (Top by Registrations) (Horizontal Bar)
- Represents: Centers ranked by registrations (optionally colored by avg deal value when available).
- Why: Volume ranking complements the composite score ranking to balance quantity vs quality/efficiency.
- Cross‑filter parameter: `sales_center_code`.
- Why cross‑filter: Choosing a center here narrows all other Tab 3 views for a focused deep‑dive.

Cross‑filter map (Tab 3):
- Sources → Targets
  - Weekly Overview → Quadrant, Tier Contribution, Top Performers, Center Performance (filters: week, category)
  - Quadrant → Overview, Tier Contribution, Top Performers, Center Performance (filter: category)
  - Tier Contribution → Overview, Quadrant, Top Performers, Center Performance (filter: tier)
  - Top Performers → Overview, Quadrant, Tier Contribution, Center Performance (filter: center)
  - Center Performance → Overview, Quadrant, Tier Contribution, Top Performers (filter: center)

---

## Rationale for Cross‑Filtering Parameters

- Week (`week_number`): Only temporal key common to all sources; synchronizes trends with mix and rankings.
- Outlet Category (`outlet_category`): Primary segmentation across multiple datasets; a driver of market share and process differences.
- Service Type (`service_type`): Operational lever that shapes speed and quality; useful for isolating process effects.
- Region/State (`region`, `state`): Geographic context impacts demand, mix, and capacity; filtering exposes network dynamics.
- Customer Category (`customer_category`): Customer mix explains demand patterns and data quality differences.
- Performance Tier (`performance_tier`): Derived classification for strategy; highlights who to learn from and where to intervene.
- Center (`sales_center_code`): Entity for actioning (coaching, recognition, resourcing); enables focused deep‑dives.

Cross‑filtering pairs graphs that share these dimensions so that selections answer natural “what if we only look at …?” questions without changing pages or running separate queries.

---

## Notes on LLM‑Backed Insights

When you click “Select this graph” under any chart, the dashboard snapshots the filtered DataFrame behind that chart (columns, limited rows, and total row count) and passes it to the LLM. The sidebar list shows the same names as each graph title so your selection and the generated report sections match one‑to‑one.

