# System Flow: Data → Charts → Interactivity → Insights (Revised)

This version clarifies two distinct month behaviors: “Combine Months” (pooled data) vs “Month Comparison” (per‑month metrics).

## Overview

- Deterministic path: SQL → DataFrames → Figures → Interactivity/drill‑downs
- LLM path: Active chart snapshot → Prompt → Gemini → Markdown insights
- Month behavior:
  - Combine Months (Normal Tabs): Pool selected months into one concatenated DataFrame with a Month column. Charts/tables/LLM reflect the pooled data.
  - Month Comparison (Compare Tab): Compute per‑month series (e.g., March vs May) from each month separately (not pooled) and render side‑by‑side.

## Detailed Flow (Text Diagram)

```
┌──────────────────┐        ┌────────────────────┐        ┌───────────────────┐
│  SQL Query Map   │──────▶ │   DB Connection    │──────▶ │  Base DataFrames  │
│ (sql_queries/*)  │        │ (SQLAlchemy Engine)│        │   (data_layer/*)  │
└──────────────────┘        └────────────────────┘        └─────────┬─────────┘
                                                                     │
                                                     Month selection │
                                                                     ▼
      ┌───────────────────────────────────────────────┬──────────────────────────────────────────────┐
      │                                               │                                              │
      │ Combine Months (Normal Tabs)                  │ Month Comparison (Compare Tab)               │
      │                                               │                                              │
      │ utils/dataframe.combine_month_frames          │ Per‑month series (no pooling):               │
      │  - Concatenate selected months per key        │  - For each selected month:                  │
      │  - Add Month column                           │    - Use that month’s DataFrame              │
      │  - Fill numeric NaNs → 0 (type stability)     │    - Compute aggregates/series               │
      │  - Safe concat (no FutureWarning)             │  - Build side‑by‑side figures/tables         │
      ▼                                               ▼                                              
┌────────────────────────┐                 ┌────────────────────────┐                                 
│ Pooled DataFrame (Tab) │                 │ March Series / May ... │                                 
└──────────────┬─────────┘                 └──────────────┬─────────┘                                 
               │                                          │                                           
               │ build figures/tables                     │ build compare bars/table                  
               ▼                                          ▼                                           
     ┌──────────────────────┐                   ┌──────────────────────┐                               
     │   Plotly Figures     │                   │   Compare Figures     │                               
     │ (app_tabs/*/figures) │                   │  (tab_compare/*)      │                               
     └──────────┬───────────┘                   └──────────┬───────────┘                               
                │                                           │                                           
     user input │ Dash callbacks                            │ Dash callbacks                           
 (filters/clicks/drill)                                     │                                           
                ▼                                           ▼                                           
┌───────────────────────────┐                   ┌───────────────────────────┐                           
│ Interactivity / Filters   │                   │ Interactivity / Filters   │                           
│ (app.py callbacks)        │                   │ (app.py callbacks)        │                           
└──────────┬────────────────┘                   └──────────┬────────────────┘                           
           │                                              │                                             
           │ capture active snapshot (pooled or per‑month)│                                             
           ▼                                              ▼                                             
┌───────────────────────────┐                   ┌───────────────────────────┐                           
│ Active Chart Snapshot     │                   │ Active Compare Snapshot   │                           
│ (columns/rows/stats/meta) │                   │ (per‑month series/stats) │                           
└──────────┬────────────────┘                   └──────────┬────────────────┘                           
           │                                              │                                             
           │ prompt construction                          │ prompt construction                         
           ▼                                              ▼                                             
┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐
│  Prompt + LLM (services/)                                                                           │
│  - build_prompt_individual / combined                                                               │
│  - Include computed stats (utils/df_summary)                                                        │
│  - Gemini (services/llm)                                                                            │
└─────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

## Modules and Responsibilities

- SQL query maps: `sql_queries/sheet1.py`, `sheet2.py`, `sheet3.py`
- Data access: `data_layer/base.py`, `data_layer/tab_*.py`
- Data utils: `utils/dataframe.py` (combine months), `utils/df_summary.py` (stats), `utils/colors.py`
- Figures/layouts: `app_tabs/tab*/figures.py`, `app_tabs/tab*/layout.py`, `app_tabs/tab_compare/*`
- App shell: `app.py` (filters, redraw, selection, month modes)
- LLM services: `services/prompts.py`, `services/insights.py`, `services/llm.py`

## Month Behavior Details

1) Combine Months (Normal Tabs)
- Pool selected months into a single DataFrame per key; add `Month` column.
- Figures and tables operate on the pooled DataFrame. They may group by `Month` when relevant.
- LLM snapshots use the pooled view so insights match the on‑screen data.

2) Month Comparison (Compare Tab)
- Compute metrics independently for each month (no pooling of values).
- Build side‑by‑side bars and a summary table (e.g., March vs May).
- LLM can consume either the per‑month series or both to describe differences explicitly.

## Data Integrity & DRY Notes

- Month concat is stable:
  - Numeric NaNs are set to 0 during month combine (original sources unchanged).
  - Concatenation temporarily drops all‑NA columns per input to avoid pandas FutureWarning, then restores column union.
- Tab 1 q2 reuses its precomputed mix to avoid recomputation in the figure phase.
