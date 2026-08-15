# 📐 Dashboard Layout & Visual Specifications Guide

This document establishes the UI/UX design standards, visual hierarchy, grid alignment, and component interaction rules for the Healthcare Claims Analytics dashboard.

## 🎨 Design System & Color Palette
* **Primary Brand (`#1F4E78`):** Utilized for primary navigation bars, card borders, and key headers to maintain a clinical enterprise aesthetic.
* **Alert Red (`#C00000`):** Reserved exclusively for **Revenue at Risk** KPIs and high-loss denial categories to draw immediate executive attention.
* **Neutral Background (`#F2F2F2`):** Background canvas color reducing visual fatigue during extended analytical reviews.
* **Card Surface (`#FFFFFF`):** Clean white container backgrounds providing high contrast for data visualizations.

---

## 📏 Grid Alignment & Spacing Rules
* **Canvas Resolution:** Fixed 1280x720 pixels (16:9 widescreen layout optimized for executive presentations and Power BI Service embedding).
* **Grid Structure:** 12-column responsive grid layout with a consistent 16px outer margin and 12px inner gutter spacing between cards.
* **Typography Hierarchy:**
  * *Dashboard Title:* Inter / Segoe UI, 18pt, Bold (`#262626`)
  * *Card Headers / Metric Labels:* Segoe UI, 11pt, Semi-Bold (`#595959`)
  * *KPI Metric Values:* Segoe UI, 24pt, Bold (`#1F4E78`)
  * *Chart Axis & Data Labels:* Segoe UI, 9pt, Regular (`#7F7F7F`)

---

## 🔄 Interactivity & Cross-Filtering Behavior
1. **Cross-Highlighting Enabled:** Selecting a specific Denial Reason Code in the Donut Chart dynamically cross-filters the Provider Leakage Bar Chart and Monthly Trends Line Chart.
2. **Drill-Through Capabilities:** Users can right-click any provider identifier (`PRVDR_NUM`) in the bar chart to drill through to grain-level claim beneficiary records.
3. **Tooltip Integration:** Hover tooltips across all visuals display exact dollar exposure, claim counts, and variance percentages.
