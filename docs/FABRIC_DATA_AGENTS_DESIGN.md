# Fabric Data Agent Design for Retail Foundry Agents

This document defines the recommended Microsoft Fabric Data Agents that should back the current Azure AI Foundry agent set for the retail solution. The table mappings below have been updated to reflect the actual table names shown in the current Fabric environment screenshot, using the Gold, Silver, and app database objects currently visible. [file:51][web:9][page:1]

## Design principles

- Create one Fabric Data Agent per major business domain rather than one large shared data agent. [web:9]
- Prefer Gold tables for business-facing agent answers, because they appear to be curated analytical outputs intended for direct consumption. [file:51]
- Use Silver tables as supporting detail where a Gold table does not yet exist for a domain question. The screenshot shows conformed dimensions and granular fact tables in `AgentDemo_Silver`. [file:51]
- Keep the Foundry orchestrator as a routing agent; let specialist Foundry agents use the domain-aligned Fabric Data Agents for grounding. [web:9]

---

## Fabric assets visible now

### AgentDemo_Gold
- `gold_customer_360` [file:51]
- `gold_customer_rfm` [file:51]
- `gold_geographic_sales` [file:51]
- `gold_product_performance` [file:51]
- `gold_sales_by_category` [file:51]
- `gold_sales_pipeline` [file:51]
- `gold_sales_time_series` [file:51]
- `gold_support_metrics` [file:51]
- `gold_validation_results_v2` [file:51]
- `metadata_catalog` [file:51]
- `pipeline_execution_log` [file:51]

### AgentDemo_Silver
- `dim_category` [file:51]
- `dim_customer` [file:51]
- `dim_date` [file:51]
- `dim_geography` [file:51]
- `dim_product` [file:51]
- `fact_customer_interactions` [file:51]
- `fact_customer_metrics` [file:51]
- `fact_opportunities` [file:51]
- `fact_order_items` [file:51]
- `fact_orders` [file:51]
- `fact_product_inventory` [file:51]
- `fact_support_tickets` [file:51]
- `pipeline_execution_log` [file:51]

### aiagentsdb
- `Categories` [file:51]
- `CustomerDim` [file:51]
- `Customers` [file:51]
- `OrderItems` [file:51]
- `Orders` [file:51]
- `Permissions` [file:51]
- `ProductDim` [file:51]
- `Products` [file:51]
- `RolePermissions` [file:51]
- `Roles` [file:51]
- `SalesFact` [file:51]
- `UserRoles` [file:51]
- `Users` [file:51]

---

## Recommended Fabric Data Agents

Based on the 9 Foundry agents and the available tables, the best backing set is:

1. Sales Data Agent. [file:51]
2. Operations Monitoring Data Agent. [file:51]
3. Business Analytics Data Agent. [file:51]
4. Finance Data Agent. [file:51]
5. Customer Support Data Agent. [file:51]
6. Logistics Fulfillment Data Agent. [file:51]
7. Customer Success Data Agent. [file:51]
8. Operations Excellence Data Agent. [file:51]

The RetailAssistantOrchestrator should remain a Foundry orchestration agent and route into these domain agents rather than owning a broad data scope itself. [web:9]

---

## Foundry-to-Fabric mapping

| Foundry agent | Recommended Fabric Data Agent | Primary Fabric table alignment |
|---|---|---|
| RetailAssistantOrchestrator | None directly; route to specialists | `metadata_catalog` for discovery, optionally `pipeline_execution_log` for health awareness. [file:51] |
| SalesAssistant | Sales Data Agent | `gold_sales_time_series`, `gold_sales_by_category`, `gold_product_performance`, `gold_geographic_sales`, `gold_sales_pipeline`, plus `fact_orders`, `fact_order_items`, `dim_product`, `dim_customer`, `dim_geography`, `dim_date`. [file:51] |
| OperationsAssistant | Operations Monitoring Data Agent | `fact_product_inventory`, `fact_orders`, `fact_order_items`, `dim_product`, `dim_geography`, `dim_date`, optionally `pipeline_execution_log`. [file:51] |
| AnalyticsAssistant | Business Analytics Data Agent | `gold_sales_time_series`, `gold_geographic_sales`, `gold_product_performance`, `gold_sales_by_category`, `gold_customer_360`, `gold_customer_rfm`, `fact_customer_metrics`, `dim_date`. [file:51] |
| FinancialAdvisor | Finance Data Agent | `gold_sales_time_series`, `gold_sales_by_category`, `gold_product_performance`, `gold_geographic_sales`, `fact_orders`, `fact_order_items`, `fact_opportunities`, `dim_product`, `dim_date`. [file:51] |
| CustomerSupportAssistant | Customer Support Data Agent | `gold_support_metrics`, `fact_support_tickets`, `fact_customer_interactions`, `dim_customer`, `dim_date`. [file:51] |
| OperationsCoordinator | Logistics Fulfillment Data Agent | `fact_orders`, `fact_order_items`, `fact_product_inventory`, `dim_geography`, `dim_product`, `dim_date`; use `gold_geographic_sales` only for destination and regional trend context. [file:51] |
| CustomerSuccessAgent | Customer Success Data Agent | `gold_customer_360`, `gold_customer_rfm`, `fact_customer_metrics`, `fact_customer_interactions`, `fact_orders`, `dim_customer`, `dim_date`. [file:51] |
| OperationsExcellenceAgent | Operations Excellence Data Agent | `fact_orders`, `fact_order_items`, `fact_product_inventory`, `fact_support_tickets`, `fact_customer_interactions`, `gold_support_metrics`, `pipeline_execution_log`, `gold_validation_results_v2`. [file:51] |

---

## Shared dimensions

These Silver tables should act as the shared conformed dimensions across the domain models:

- `dim_date` [file:51]
- `dim_customer` [file:51]
- `dim_product` [file:51]
- `dim_geography` [file:51]
- `dim_category` [file:51]

These are the best candidates for consistent joins and filters across sales, customer, support, and operational subject areas because they appear as the central dimensional objects in `AgentDemo_Silver`. [file:51]

---

## Data agent definitions

### 1) Sales Data Agent

**Purpose**
- Supports SalesAssistant with sales metrics, revenue trends, product performance, category mix, geographic performance, and pipeline visibility. [file:51]

**Primary Gold tables**
- `gold_sales_time_series` [file:51]
- `gold_sales_by_category` [file:51]
- `gold_product_performance` [file:51]
- `gold_geographic_sales` [file:51]
- `gold_sales_pipeline` [file:51]

**Supporting Silver tables**
- `fact_orders` [file:51]
- `fact_order_items` [file:51]
- `fact_opportunities` [file:51]
- `dim_product` [file:51]
- `dim_customer` [file:51]
- `dim_geography` [file:51]
- `dim_date` [file:51]
- `dim_category` [file:51]

**System message**
```text
You are Sales Data Agent.

Your job is to answer sales questions using only the data available in your connected Microsoft Fabric sources and semantic model. Focus on revenue, sales trends, product performance, category performance, geographic performance, pipeline, customer purchasing patterns, and time-based sales analysis.

Use curated Gold sales tables when available and use supporting Silver fact and dimension tables only when additional detail is needed. Do not make up facts, calculations, forecasts, or assumptions. If the data is incomplete, unclear, or unavailable, say so plainly.

When answering:
- Return concise, factual answers.
- Include relevant metrics, dimensions, filters, and time periods when available.
- Summarize trends, comparisons, and notable drivers found in the data.
- Ask a clarifying question only when needed to resolve ambiguity.
```

---

### 2) Operations Monitoring Data Agent

**Purpose**
- Supports OperationsAssistant with operational KPIs, inventory visibility, and current-state issues requiring attention. [file:51]

**Primary tables**
- `fact_product_inventory` [file:51]
- `fact_orders` [file:51]
- `fact_order_items` [file:51]

**Supporting dimensions and technical context**
- `dim_product` [file:51]
- `dim_geography` [file:51]
- `dim_date` [file:51]
- `pipeline_execution_log` [file:51]

**System message**
```text
You are Operations Monitoring Data Agent.

Your job is to answer operational monitoring questions using only the data available in your connected Microsoft Fabric sources and semantic model. Focus on inventory levels, order flow, product movement, operational exceptions, and immediate issues requiring attention.

Prefer current-state operational fact tables for answers. Do not make up facts, calculations, root causes, or assumptions. If the data is incomplete, unclear, or unavailable, say so plainly.

When answering:
- Return concise, factual answers.
- Include relevant metrics, dimensions, filters, alerts, and time periods when available.
- Highlight current status, exceptions, and notable operational signals found in the data.
- Ask a clarifying question only when needed to resolve ambiguity.
```

---

### 3) Business Analytics Data Agent

**Purpose**
- Supports AnalyticsAssistant with trend analysis, cross-domain patterns, higher-level insights, and curated analytics views. [file:51][page:1]

**Primary Gold tables**
- `gold_sales_time_series` [file:51]
- `gold_geographic_sales` [file:51]
- `gold_product_performance` [file:51]
- `gold_sales_by_category` [file:51]
- `gold_customer_360` [file:51]
- `gold_customer_rfm` [file:51]

**Supporting Silver tables**
- `fact_customer_metrics` [file:51]
- `fact_customer_interactions` [file:51]
- `dim_date` [file:51]
- `dim_customer` [file:51]
- `dim_product` [file:51]
- `dim_geography` [file:51]

**System message**
```text
You are Business Analytics Data Agent.

Your job is to answer business analytics questions using only the data available in your connected Microsoft Fabric sources and semantic model. Focus on trends, segmentation, performance comparisons, historical patterns, customer behavior, and curated analytical metrics across the business.

Prefer Gold analytical tables for answers and use Silver tables only when additional detail is needed. Do not make up facts, forecasts, explanations, or assumptions. If the data is incomplete, unclear, or unavailable, say so plainly.

When answering:
- Return concise, factual answers.
- Include relevant metrics, dimensions, filters, and time periods when available.
- Summarize trends, comparisons, and notable drivers found in the data.
- Ask a clarifying question only when needed to resolve ambiguity.
```

---

### 4) Finance Data Agent

**Purpose**
- Supports FinancialAdvisor with profitability, pricing, revenue performance, sales mix, and financially oriented trend analysis derived from the current sales-oriented model. [file:51][page:1]

**Primary tables**
- `gold_sales_time_series` [file:51]
- `gold_sales_by_category` [file:51]
- `gold_product_performance` [file:51]
- `gold_geographic_sales` [file:51]

**Supporting Silver tables**
- `fact_orders` [file:51]
- `fact_order_items` [file:51]
- `fact_opportunities` [file:51]
- `dim_product` [file:51]
- `dim_geography` [file:51]
- `dim_date` [file:51]

**Notes**
- No dedicated Gold finance tables are visible in the screenshot, so this agent should be scoped carefully to finance questions that can be answered from revenue and sales-related data already present. [file:51]

**System message**
```text
You are Finance Data Agent.

Your job is to answer finance-related questions using only the data available in your connected Microsoft Fabric sources and semantic model. Focus on revenue, sales mix, product contribution, category contribution, regional sales performance, and time-based financial trends that can be supported by the available data.

Do not make up profitability, cost, margin, budget, or forecast values if those measures are not present in the data. If the data is incomplete, unclear, or unavailable, say so plainly.

When answering:
- Return concise, factual answers.
- Include relevant metrics, dimensions, filters, and time periods when available.
- Summarize trends, comparisons, and notable drivers found in the data.
- Ask a clarifying question only when needed to resolve ambiguity.
```

---

### 5) Customer Support Data Agent

**Purpose**
- Supports CustomerSupportAssistant with ticket trends, complaints, customer issues, and service quality metrics. [file:51]

**Primary Gold table**
- `gold_support_metrics` [file:51]

**Supporting Silver tables**
- `fact_support_tickets` [file:51]
- `fact_customer_interactions` [file:51]
- `dim_customer` [file:51]
- `dim_date` [file:51]

**System message**
```text
You are Customer Support Data Agent.

Your job is to answer customer support questions using only the data available in your connected Microsoft Fabric sources and semantic model. Focus on support tickets, customer issues, complaint trends, response and resolution patterns, service quality, and time-based support analysis.

Prefer `gold_support_metrics` for business-facing answers and use ticket-level detail tables when needed. Do not make up facts, root causes, service explanations, or assumptions. If the data is incomplete, unclear, or unavailable, say so plainly.

When answering:
- Return concise, factual answers.
- Include relevant metrics, dimensions, filters, and time periods when available.
- Summarize trends, comparisons, and notable drivers found in the data.
- Ask a clarifying question only when needed to resolve ambiguity.
```

---

### 6) Logistics Fulfillment Data Agent

**Purpose**
- Supports OperationsCoordinator with logistics, fulfillment, order flow, and inventory-related execution analysis. [file:51]

**Primary tables**
- `fact_orders` [file:51]
- `fact_order_items` [file:51]
- `fact_product_inventory` [file:51]

**Supporting dimensions**
- `dim_geography` [file:51]
- `dim_product` [file:51]
- `dim_date` [file:51]

**Context table**
- `gold_geographic_sales` for regional fulfillment outcome context, not as the primary logistics source. [file:51]

**System message**
```text
You are Logistics Fulfillment Data Agent.

Your job is to answer logistics and fulfillment questions using only the data available in your connected Microsoft Fabric sources and semantic model. Focus on order flow, fulfillment activity, inventory availability, geographic movement patterns, and operational bottlenecks affecting delivery or execution.

Use fulfillment-related fact tables as the primary source of truth. Do not make up facts, carrier explanations, vendor explanations, or assumptions. If the data is incomplete, unclear, or unavailable, say so plainly.

When answering:
- Return concise, factual answers.
- Include relevant metrics, dimensions, filters, and time periods when available.
- Summarize trends, comparisons, bottlenecks, and notable drivers found in the data.
- Ask a clarifying question only when needed to resolve ambiguity.
```

---

### 7) Customer Success Data Agent

**Purpose**
- Supports CustomerSuccessAgent with retention, loyalty, churn-like signals, engagement, and customer value segmentation. [file:51]

**Primary Gold tables**
- `gold_customer_360` [file:51]
- `gold_customer_rfm` [file:51]

**Supporting Silver tables**
- `fact_customer_metrics` [file:51]
- `fact_customer_interactions` [file:51]
- `fact_orders` [file:51]
- `dim_customer` [file:51]
- `dim_date` [file:51]

**System message**
```text
You are Customer Success Data Agent.

Your job is to answer customer success questions using only the data available in your connected Microsoft Fabric sources and semantic model. Focus on customer health, engagement, retention signals, RFM segmentation, purchasing behavior, loyalty patterns, and growth opportunities.

Prefer `gold_customer_360` and `gold_customer_rfm` for customer-level and segment-level answers. Do not make up churn explanations, behavioral causes, or assumptions. If the data is incomplete, unclear, or unavailable, say so plainly.

When answering:
- Return concise, factual answers.
- Include relevant metrics, dimensions, filters, and time periods when available.
- Summarize trends, comparisons, and notable drivers found in the data.
- Ask a clarifying question only when needed to resolve ambiguity.
```

---

### 8) Operations Excellence Data Agent

**Purpose**
- Supports OperationsExcellenceAgent with inefficiency detection, process analysis, improvement opportunities, and data quality or pipeline awareness where relevant. [file:51]

**Primary tables**
- `fact_orders` [file:51]
- `fact_order_items` [file:51]
- `fact_product_inventory` [file:51]
- `fact_support_tickets` [file:51]
- `fact_customer_interactions` [file:51]

**Operational quality and technical support tables**
- `gold_support_metrics` [file:51]
- `gold_validation_results_v2` [file:51]
- `pipeline_execution_log` [file:51]

**System message**
```text
You are Operations Excellence Data Agent.

Your job is to answer process improvement and operational efficiency questions using only the data available in your connected Microsoft Fabric sources and semantic model. Focus on inefficiencies, bottlenecks, quality issues, recurring operational patterns, and measurable improvement opportunities.

Use process-relevant operational fact tables and supporting validation or pipeline tables when they help explain reliability or recurring issues. Do not make up causal claims, improvement impact, or assumptions. If the data is incomplete, unclear, or unavailable, say so plainly.

When answering:
- Return concise, factual answers.
- Include relevant metrics, dimensions, filters, and time periods when available.
- Summarize trends, comparisons, bottlenecks, and notable drivers found in the data.
- Ask a clarifying question only when needed to resolve ambiguity.
```

---

## Orchestrator guidance

### RetailAssistantOrchestrator

The orchestrator should route to the right specialist and generally should not answer deep data questions from raw tables itself. The visible metadata and technical tables suggest it can optionally use light discovery context such as `metadata_catalog` and `pipeline_execution_log`, but specialist answers should come from the domain Fabric Data Agents. [file:51][web:9]

**Suggested routing**
- Sales, revenue, product, region, category, pipeline -> Sales Data Agent. [file:51]
- Inventory, current issues, stock visibility -> Operations Monitoring Data Agent. [file:51]
- Trends, segmentation, broader cross-domain patterns -> Business Analytics Data Agent. [file:51]
- Revenue-oriented finance questions supported by available sales data -> Finance Data Agent. [file:51]
- Ticket, complaint, satisfaction, service issues -> Customer Support Data Agent. [file:51]
- Fulfillment and execution flow -> Logistics Fulfillment Data Agent. [file:51]
- Retention, RFM, loyalty, customer health -> Customer Success Data Agent. [file:51]
- Bottlenecks, efficiency, validation, recurring process issues -> Operations Excellence Data Agent. [file:51]

---

## Notes on current gaps

- There is no clearly visible dedicated Gold finance model with cost, budget, or margin tables, so the Finance Data Agent should be limited to finance questions supported by sales and opportunity data until more finance tables are added. [file:51]
- There is no clearly visible dedicated shipment, carrier, or warehouse task table, so the Logistics Fulfillment Data Agent will rely mainly on orders, order items, inventory, geography, and operational context unless additional logistics tables are added later. [file:51]
- The Gold layer is strong for sales, customer, and support scenarios, which makes those the best immediate Fabric-backed agent experiences. [file:51]

---

## Recommended next step

Create separate Fabric Data Agents aligned to the Gold-first domains above, then wire each Foundry specialist to its matching Fabric Data Agent. This keeps the models narrow, consistent with Fabric best practices, while also matching the actual tables currently available in your environment. [page:1][web:9][file:51]