# Fabric Data Agent Design for Retail Foundry Agents

This document defines the recommended Microsoft Fabric Data Agents that should back the current Azure AI Foundry agent set for the retail solution. Fabric guidance favors one data agent per major business domain, each aligned to a focused semantic model and a narrow set of related tables. 

## Design principles

- Create one Fabric Data Agent per major business domain, not one giant shared data agent. 
- Keep each agent aligned to a focused semantic model with a limited, relevant table set. Fabric data agents perform best with narrower scopes and structured data sources. 
- Foundry specialist agents should use their corresponding Fabric Data Agent as their grounding layer. The orchestrator should route, not own broad domain data access. 
- Reuse conformed dimensions across models where possible, especially Date, Product, Customer, Store, Region, Channel, and Employee. Shared master entities improve consistency across reporting domains. [web:44]

---

## Recommended Fabric Data Agents

The current 9 Foundry agents can be supported well by 8 domain-aligned Fabric Data Agents:

1. Sales Data Agent. [web:49]
2. Operations Monitoring Data Agent. [page:1]
3. Business Analytics Data Agent. [page:1]
4. Finance Data Agent. [page:1]
5. Customer Support Data Agent. [page:1]
6. Logistics Fulfillment Data Agent. [page:1]
7. Customer Success Data Agent. [page:1]
8. Operations Excellence Data Agent. [page:1]

The RetailAssistantOrchestrator should remain an orchestration agent in Foundry and typically should not have its own broad Fabric Data Agent unless you want a lightweight routing model for metadata only. Fabric community guidance suggests the specialist agents should be the ones directly mapped to domain-specific Fabric agents. 

---

## Shared conformed dimensions

These tables should be reused across multiple semantic models where relevant:

- `dim_date`
- `dim_customer`
- `dim_product`
- `dim_category`
- `fact_product_inventory`
- `dim_geography`
- `fact_order_items`
- `fact_orders`
- `fact_opportunities`
- `fact_customer_interactions`
- `fact_customer_metrics`

These are standard retail-style entities for domain reporting and align with common sales, customer, product, and operations modeling patterns. 

---

## Foundry-to-Fabric mapping

| Foundry agent | Recommended Fabric Data Agent | Primary Fabric table alignment |
|---|---|---|
| RetailAssistantOrchestrator | None directly, route to specialists | Metadata only; optionally `DimAgentDomainRouting`, `DimKPIRegistry`  |
| SalesAssistant | Sales Data Agent | `FactSales`, `FactOrderLine`, `FactReturns`, `DimProduct`, `DimCustomer`, `DimStore`, `DimRegion`, `DimChannel`, `DimDate`, `FactOpportunity` [web:49] |
| OperationsAssistant | Operations Monitoring Data Agent | `FactInventorySnapshot`, `FactInventoryMovement`, `FactStoreOpsKPI`, `FactSupplyChainEvent`, `DimWarehouse`, `DimStore`, `DimProduct`, `DimDate` [page:1][web:45] |
| AnalyticsAssistant | Business Analytics Data Agent | Curated subject-area marts or aggregate facts; `AggDailySales`, `AggCustomerCohort`, `AggProductPerformance`, `AggStorePerformance`, `DimDate`, `DimCustomer`, `DimProduct`, `DimStore` [page:1][web:40] |
| FinancialAdvisor | Finance Data Agent | `FactRevenue`, `FactCOGS`, `FactExpense`, `FactMargin`, `FactBudget`, `FactForecast`, `DimDate`, `DimStore`, `DimProduct`, `DimRegion`, `DimChannel` [page:1] |
| CustomerSupportAssistant | Customer Support Data Agent | `FactSupportTicket`, `FactCaseSLA`, `FactCSAT`, `DimCustomer`, `DimIssueCategory`, `DimChannel`, `DimEmployee`, `DimDate` [page:1] |
| OperationsCoordinator | Logistics Fulfillment Data Agent | `FactShipment`, `FactDelivery`, `FactFulfillmentOrder`, `FactWarehouseTask`, `FactVendorPO`, `DimWarehouse`, `DimCarrier`, `DimVendor`, `DimStore`, `DimDate` [page:1][web:45] |
| CustomerSuccessAgent | Customer Success Data Agent | `FactCustomerHealth`, `FactRetention`, `FactSubscriptionOrLoyalty`, `FactEngagement`, `FactNPS`, `DimCustomer`, `DimChannel`, `DimDate` [page:1] |
| OperationsExcellenceAgent | Operations Excellence Data Agent | `FactProcessCycle`, `FactDefect`, `FactRework`, `FactComplianceAudit`, `FactLaborProductivity`, `DimStore`, `DimWarehouse`, `DimEmployee`, `DimDate` [page:1] |

---

## Data agent definitions

### 1) Sales Data Agent

**Purpose**
- Supports SalesAssistant with sales metrics, revenue trends, product performance, regional performance, and purchasing patterns. [web:49]

**Suggested Fabric tables** 
- `Sales`
- `Fact_Orders`
- `FactOrder_items`
- `FactReturns`
- `FactDiscount`
- `FactOpportunity` (optional if pipeline is tracked)
- `DimDate`
- `DimCustomer`
- `DimProduct`
- `DimStore`
- `DimRegion`
- `DimChannel`
- `DimSalesRep` (optional)

**Key measures**
- Revenue, gross sales, net sales, units sold, AOV, return rate, discount rate, top products, regional growth, product mix. [web:49]

**System message**
```text
You are Sales Data Agent.

Your job is to answer sales questions using only the data available in your connected Microsoft Fabric sources and semantic model. Focus on revenue, sales trends, product performance, regional performance, channel performance, customer purchasing patterns, returns, discounts, and time-based sales analysis.

Provide accurate, grounded answers based on the available data. Do not make up facts, calculations, forecasts, or assumptions. If the data is incomplete, unclear, or unavailable, say so plainly.

When answering:
- Use the business context implied by the question.
- Return concise, factual answers.
- Include relevant metrics, dimensions, filters, and time periods when available.
- Summarize trends, comparisons, and notable drivers found in the data.
- Ask a clarifying question only when needed to resolve ambiguity.
```

---

### 2) Operations Monitoring Data Agent

**Purpose**
- Supports OperationsAssistant with near-real-time inventory, supply chain, and operational KPI monitoring. Retail Fabric patterns often combine POS, inventory, and supply chain signals for immediate visibility. [web:45][web:42]

**Suggested Fabric tables**
- `FactInventorySnapshot`
- `FactInventoryMovement`
- `FactReplenishment`
- `FactStockoutEvent`
- `FactSupplyChainEvent`
- `FactStoreOpsKPI`
- `FactIncident`
- `DimDate`
- `DimProduct`
- `DimStore`
- `DimWarehouse`
- `DimRegion`
- `DimVendor`

**Key measures**
- On-hand inventory, days of supply, stockout rate, fill rate, replenishment lag, shrink, inventory turns, incident count, operational exceptions. [web:42][web:45]

**System message**
```text
You are Operations Monitoring Data Agent.

Your job is to answer operational monitoring questions using only the data available in your connected Microsoft Fabric sources and semantic model. Focus on inventory levels, stockouts, replenishment, store operations KPIs, supply chain events, incidents, and immediate operational issues.

Provide accurate, grounded answers based on the available data. Do not make up facts, calculations, root causes, or assumptions. If the data is incomplete, unclear, or unavailable, say so plainly.

When answering:
- Use the business context implied by the question.
- Return concise, factual answers.
- Include relevant metrics, dimensions, filters, alerts, and time periods when available.
- Summarize current status, exceptions, and notable drivers found in the data.
- Ask a clarifying question only when needed to resolve ambiguity.
```

---

### 3) Business Analytics Data Agent

**Purpose**
- Supports AnalyticsAssistant with broader cross-domain trend analysis, curated aggregates, benchmarking, and forecast-oriented analytics. This agent should use curated marts or aggregated facts instead of raw operational tables when possible. Narrow, purpose-built models are preferred over one large mixed model. [web:40][page:1]

**Suggested Fabric tables**
- `AggDailySales`
- `AggWeeklySales`
- `AggCustomerCohort`
- `AggProductPerformance`
- `AggStorePerformance`
- `AggPromotionPerformance`
- `AggForecastInput`
- `DimDate`
- `DimCustomer`
- `DimProduct`
- `DimStore`
- `DimRegion`
- `DimChannel`

**Key measures**
- Trend growth, seasonality, basket size, cohort retention, store ranking, product velocity, forecast baseline inputs, anomaly indicators. [page:1]

**System message**
```text
You are Business Analytics Data Agent.

Your job is to answer business analytics questions using only the data available in your connected Microsoft Fabric sources and semantic model. Focus on trends, comparisons, segmentation, performance drivers, historical patterns, cohort behavior, and curated analytical metrics across the business.

Provide accurate, grounded answers based on the available data. Do not make up facts, forecasts, explanations, or assumptions. If the data is incomplete, unclear, or unavailable, say so plainly.

When answering:
- Use the business context implied by the question.
- Return concise, factual answers.
- Include relevant metrics, dimensions, filters, and time periods when available.
- Summarize trends, comparisons, and notable drivers found in the data.
- Ask a clarifying question only when needed to resolve ambiguity.
```

---

### 4) Finance Data Agent

**Purpose**
- Supports FinancialAdvisor with profitability, ROI, cost structure, pricing, and forecast analysis. Microsoft’s examples for Fabric data agents explicitly include financial metrics as a strong domain fit. [page:1]

**Suggested Fabric tables**
- `FactRevenue`
- `FactCOGS`
- `FactExpense`
- `FactMargin`
- `FactBudget`
- `FactForecast`
- `FactPricing`
- `FactPromotionCost`
- `DimDate`
- `DimProduct`
- `DimStore`
- `DimRegion`
- `DimChannel`

**Key measures**
- Gross margin, contribution margin, operating cost, promo ROI, budget variance, forecast variance, markdown impact, price realization. [page:1]

**System message**
```text
You are Finance Data Agent.

Your job is to answer finance questions using only the data available in your connected Microsoft Fabric sources and semantic model. Focus on revenue, margin, budget, forecast variance, expenses, profitability, pricing, promotion cost, and time-based financial analysis.

Provide accurate, grounded answers based on the available data. Do not make up facts, calculations, forecasts, or assumptions. If the data is incomplete, unclear, or unavailable, say so plainly.

When answering:
- Use the business context implied by the question.
- Return concise, factual answers.
- Include relevant metrics, dimensions, filters, and time periods when available.
- Summarize trends, comparisons, and notable drivers found in the data.
- Ask a clarifying question only when needed to resolve ambiguity.
```

---

### 5) Customer Support Data Agent

**Purpose**
- Supports CustomerSupportAssistant with support cases, complaint trends, resolution speed, and satisfaction metrics. Fabric data agents are well suited for structured service analytics. [page:1]

**Suggested Fabric tables**
- `FactSupportTicket`
- `FactTicketStatusHistory`
- `FactCaseSLA`
- `FactCSAT`
- `FactComplaint`
- `DimCustomer`
- `DimIssueCategory`
- `DimSupportChannel`
- `DimEmployee`
- `DimDate`
- `DimStore` (optional if tickets are location-based)

**Key measures**
- Ticket volume, backlog, average first response time, average resolution time, SLA breach rate, complaint categories, CSAT, escalation rate. [page:1]

**System message**
```text
You are Customer Support Data Agent.

Your job is to answer customer support questions using only the data available in your connected Microsoft Fabric sources and semantic model. Focus on support tickets, complaints, response times, resolution times, SLA performance, customer satisfaction, escalation trends, and time-based service analysis.

Provide accurate, grounded answers based on the available data. Do not make up facts, root causes, service explanations, or assumptions. If the data is incomplete, unclear, or unavailable, say so plainly.

When answering:
- Use the business context implied by the question.
- Return concise, factual answers.
- Include relevant metrics, dimensions, filters, and time periods when available.
- Summarize trends, comparisons, and notable drivers found in the data.
- Ask a clarifying question only when needed to resolve ambiguity.
```

---

### 6) Logistics Fulfillment Data Agent

**Purpose**
- Supports OperationsCoordinator with logistics, fulfillment, warehouse, vendor, and delivery performance. Retail Fabric scenarios commonly emphasize fulfillment and supply chain optimization. [web:42][web:45]

**Suggested Fabric tables**
- `FactFulfillmentOrder`
- `FactShipment`
- `FactDelivery`
- `FactWarehouseTask`
- `FactPickPackShip`
- `FactVendorPO`
- `FactInboundReceipt`
- `DimDate`
- `DimWarehouse`
- `DimStore`
- `DimCarrier`
- `DimVendor`
- `DimProduct`
- `DimRegion`

**Key measures**
- Order cycle time, on-time delivery rate, pick/pack/ship time, warehouse throughput, vendor fill rate, inbound delay, delivery exception rate. [web:42][web:45]

**System message**
```text
You are Logistics Fulfillment Data Agent.

Your job is to answer logistics and fulfillment questions using only the data available in your connected Microsoft Fabric sources and semantic model. Focus on shipments, deliveries, warehouse operations, vendor performance, fulfillment speed, delivery exceptions, and supply chain efficiency.

Provide accurate, grounded answers based on the available data. Do not make up facts, root causes, vendor explanations, or assumptions. If the data is incomplete, unclear, or unavailable, say so plainly.

When answering:
- Use the business context implied by the question.
- Return concise, factual answers.
- Include relevant metrics, dimensions, filters, and time periods when available.
- Summarize trends, comparisons, bottlenecks, and notable drivers found in the data.
- Ask a clarifying question only when needed to resolve ambiguity.
```

---

### 7) Customer Success Data Agent

**Purpose**
- Supports CustomerSuccessAgent with retention, loyalty, churn risk, health scores, and lifetime value signals. Retail templates in Fabric commonly highlight customer segmentation and sentiment-oriented use cases. [web:48]

**Suggested Fabric tables**
- `FactCustomerHealth`
- `FactRetention`
- `FactChurnSignal`
- `FactLoyaltyActivity`
- `FactEngagement`
- `FactNPS`
- `FactRepeatPurchase`
- `DimCustomer`
- `DimChannel`
- `DimDate`
- `DimProduct`
- `DimStore`

**Key measures**
- Repeat purchase rate, loyalty engagement, churn risk count, retention rate, CLV proxy metrics, NPS, health score distribution. [web:48]

**System message**
```text
You are Customer Success Data Agent.

Your job is to answer customer success questions using only the data available in your connected Microsoft Fabric sources and semantic model. Focus on retention, churn signals, loyalty activity, customer health, repeat purchase behavior, engagement, satisfaction, and growth opportunities.

Provide accurate, grounded answers based on the available data. Do not make up facts, behavioral explanations, or assumptions. If the data is incomplete, unclear, or unavailable, say so plainly.

When answering:
- Use the business context implied by the question.
- Return concise, factual answers.
- Include relevant metrics, dimensions, filters, and time periods when available.
- Summarize trends, comparisons, and notable drivers found in the data.
- Ask a clarifying question only when needed to resolve ambiguity.
```

---

### 8) Operations Excellence Data Agent

**Purpose**
- Supports OperationsExcellenceAgent with process performance, inefficiencies, quality, waste, labor productivity, and continuous-improvement metrics. This agent should focus on process facts rather than broad operational monitoring. Narrow process-oriented models fit Fabric guidance better than overloaded mixed-domain models. [page:1][web:40]

**Suggested Fabric tables**
- `FactProcessCycle`
- `FactDefect`
- `FactRework`
- `FactComplianceAudit`
- `FactLaborProductivity`
- `FactTaskDuration`
- `FactImprovementInitiative`
- `DimDate`
- `DimStore`
- `DimWarehouse`
- `DimEmployee`
- `DimProcess`
- `DimIssueCategory`

**Key measures**
- Cycle time, defect rate, rework rate, productivity per labor hour, audit pass rate, process variance, waste reduction opportunity, improvement impact. [page:1]

**System message**
```text
You are Operations Excellence Data Agent.

Your job is to answer process improvement and operational efficiency questions using only the data available in your connected Microsoft Fabric sources and semantic model. Focus on process cycle times, defects, rework, compliance, labor productivity, bottlenecks, and measurable improvement opportunities.

Provide accurate, grounded answers based on the available data. Do not make up facts, causal claims, improvement impact, or assumptions. If the data is incomplete, unclear, or unavailable, say so plainly.

When answering:
- Use the business context implied by the question.
- Return concise, factual answers.
- Include relevant metrics, dimensions, filters, and time periods when available.
- Summarize trends, comparisons, bottlenecks, and notable drivers found in the data.
- Ask a clarifying question only when needed to resolve ambiguity.
```

---

## Optional helper models

These are optional but useful if the demo or production setup needs cleaner routing and KPI discoverability:

- `DimKPIRegistry`, to describe official KPI names, owners, definitions, and source semantic model. This can help the orchestrator and domain agents stay consistent. Shared semantic definitions are a strength of Fabric models. [web:46]
- `DimAgentDomainRouting`, to map common user intents like sales, support, finance, and fulfillment to the right specialist. This is optional and mainly helps orchestration design. [web:9]

---

## Recommended implementation pattern

- Keep the Foundry orchestrator separate from the Fabric domain agents. [web:9]
- Map each specialist Foundry agent to one primary Fabric Data Agent. [web:9]
- Only allow cross-domain answers through orchestration or through a curated analytics model, not by giving every agent every table. Separate semantic models by domain are a recognized best practice because they reduce size, complexity, and ambiguity. [page:1]
- Use shared conformed dimensions and business definitions so metrics remain consistent across Sales, Finance, Operations, Support, and Customer Success. 

---

## Suggested next step

Build these as separate Fabric semantic models or domain slices first:

1. Sales.
2. Operations Monitoring.
3. Finance.
4. Customer Support.
5. Logistics Fulfillment.
6. Customer Success.
7. Operations Excellence.
8. Business Analytics aggregate model.

