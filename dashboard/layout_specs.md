# 🏥 Executive Healthcare Claims Analytics & RCM Dashboard

[![Power BI Service](https://img.shields.io/badge/Platform-Power%20BI-yellow?style=flat-square&logo=powerbi)](https://powerbi.microsoft.com)
[![Widescreen 16:9](https://img.shields.io/badge/Resolution-1280x720-blue?style=flat-square)](https://www.w3schools.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

An executive-level **Revenue Cycle Management (RCM) and Claims Denial Intelligence** dashboard optimized for 1280x720 widescreen presentation, executive board reviews, and Power BI Service embedding.

---

## 🎨 Design System & Color Palette

| Token | Hex | Role / Application |
|---|---|---|
| **Primary Brand** | `#1F4E78` | Navigation bars, card borders, key headers |
| **Alert Red** | `#C00000` | Reserved for **Revenue at Risk** KPIs & high-loss denial categories |
| **Neutral Background** | `#F2F2F2` | Canvas background to reduce visual fatigue |
| **Card Surface** | `#FFFFFF` | Container backgrounds for high contrast data visualization |

---

## 📏 Grid Specifications & Typography
- **Resolution:** 1280 × 720 pixels (16:9 widescreen layout)
- **Grid Layout:** 12-column responsive grid with a 16px outer margin and 12px inner gutter spacing.
- **Typography Hierarchy:**
  - *Dashboard Title:* Segoe UI / Inter, 18pt, Bold (`#262626`)
  - *Card Headers / Metric Labels:* Segoe UI, 11pt, Semi-Bold (`#595959`)
  - *KPI Metric Values:* Segoe UI, 24pt, Bold (`#1F4E78`)
  - *Chart Axis & Data Labels:* Segoe UI, 9pt, Regular (`#7F7F7F`)

---

## 📦 Layout Grid Structure

| Row | Container | Height (px) | Contents & Specifications |
|---|---|---|---|
| **1** | `header_container` | 80 | **Title Banner:** "Executive RCM & Claims Denial Intelligence" (12-column span) |
| **2** | `kpi_row_container` | 120 | **4 KPI Cards (3 columns each):** Total Billed, Total Collected, Revenue at Risk (Alert Red), Denial Rate |
| **3** | `visuals_row_container` | 480 | **3 Analytical Visuals (4 columns each):**<br>• Donut Chart: Denial Breakdown by Reason Code<br>• Line/Column Chart: Monthly Trends<br>• Bar Chart: Top-10 Provider Leakage (`PRVDR_NUM`) |

---

## 🔄 Interactivity & Cross-Filtering Rules
1. **Cross-Highlighting:** Selecting a specific Denial Reason Code in the Donut Chart dynamically cross-filters the Provider Leakage Bar Chart and Monthly Trends Line Chart.
2. **Drill-Through Actions:** Right-clicking any provider identifier (`PRVDR_NUM`) in the bar chart allows instant drill-through to grain-level claim beneficiary records.
3. **Advanced Tooltips:** Hover states surface exact dollar exposure, claim volumes, and period-over-period variance percentages.

---

## 🚀 Quick Start Deployment
1. Import the custom color palette using the provided `theme.json` file inside Power BI Desktop.
2. Structure your data model using the field bindings defined in `layout_config.json`.
3. Publish to Power BI Service with widescreen canvas settings enabled (1280x720 fixed layout).
