# Fabric Data Agent Deployment — Step-by-Step Guide

This guide walks you through deploying a **Fabric Data Agent** in a way that is easier for a first-time implementer to follow. It explains what to prepare, what to click, how to validate the agent, and how to prove the app is actually using the curated Fabric data path.

---

## What You Are Building

A Fabric Data Agent lets users ask business questions in natural language against approved Fabric data sources.

In this deployment, the goal is to:

1. Point the Data Agent at a **curated Gold data source**.
2. Limit it to only approved business-facing tables.
3. Add clear instructions so the agent stays in scope.
4. Validate it inside Fabric.
5. Connect it to **Azure AI Foundry**.
6. Connect the app runtime to Foundry.
7. Prove the app is using the Data Agent path rather than an old SQL-only route.

---

## Before You Start

Before creating the Data Agent, confirm the platform is ready.

### Required prerequisites

- [ ] Your Fabric capacity is **paid F2 or higher**.
- [ ] The **Fabric Data Agent** tenant setting is enabled.
- [ ] The **Copilot** tenant setting is enabled if your environment requires it.
- [ ] **Cross-geo processing for AI** is enabled if required by your tenant setup.
- [ ] **Cross-geo storing for AI** is enabled if required by your tenant setup.
- [ ] Your Fabric workspace already contains the curated source you want the agent to use.

### Supported source types

The source you attach to the Data Agent should be one of these supported types:

| Source type | Typical use |
|---|---|
| **Lakehouse** | When your Gold tables are stored directly in Fabric lakehouse tables |
| **Warehouse** | When your governed reporting path is warehouse-first |
| **Power BI semantic model** | Best when business logic and measures are already validated there |
| **KQL database** | Best for operational or event-based analytics scenarios |

> **Best first choice:** Use a validated **Gold semantic model** if you already have one. If not, use Gold Lakehouse or Gold Warehouse tables. Avoid Bronze or Silver data for the first production agent.

---

## Step 1 — Decide Which Source to Expose

Before creating the agent, choose the exact source it will be allowed to answer from.

### Recommended order

1. **Gold semantic model** — best option if measures and business logic are already validated.
2. **Gold Lakehouse tables** — good option if the semantic model is not ready yet.
3. **Gold Warehouse tables** — good option if this is your governed SQL/reporting path.

### What to avoid

Do **not** use these for the first production version:

- Bronze data.
- Silver data.
- Raw ingestion tables.
- Experimental or partially validated sources.

> **Why this matters:** The Data Agent can only be trusted if its source is already trusted. A well-written agent on top of unstable data will still produce unstable answers.

---

## Step 2 — Create the Fabric Data Agent

Now create the Data Agent item in your Fabric workspace.

1. Open your **Fabric workspace**.
2. Click **+ New item**.
3. Search for **Fabric data agent**.
4. Select it.
5. Enter a clear, business-friendly name such as:
   - `Sales Insights Agent`
   - `Customer Analytics Agent`
   - `Support Operations Agent`
6. Click **Create**.

After the item is created, Fabric opens the **OneLake catalog** so you can attach data sources.

> **Tip:** Name the agent based on the business domain, not the technology. This makes it easier for users to know what it is for.

---

## Step 3 — Add the Data Source

Next, attach the approved source to the agent.

1. In the **OneLake catalog**, browse to the validated source you selected in Step 1.
2. Click **Add**.
3. Wait for the source to appear in the Data Agent configuration.
4. Only add a second source if there is a clear business reason to do so.

### Important guidance

- Keep the first version narrow.
- Fabric Data Agent can support up to **five sources**, but your first deployment should usually use **one trusted source**.
- If you use a **semantic model**, confirm you have the permissions required to add and use it.

> **Why this matters:** The more sources you expose, the harder it becomes to validate what the agent is using and why it gave a certain answer.

---

## Step 4 — Select Only the Approved Tables

After adding the source, choose exactly which tables the agent is allowed to use.

1. In the left **Explorer** pane, open the added source.
2. Review the available tables.
3. Select only the tables the agent should be allowed to answer questions about.

### Recommended first table set

| Table | Purpose |
|---|---|
| `gold_customer360` | Customer profile and customer-level metrics |
| `gold_productperformance` | Product-level business performance |
| `goldsalesbycategory` | Sales by category |
| `goldsalestimeseries` | Sales over time |
| `goldsupportmetrics` | Support KPI and service metrics |

> **Best practice:** The smaller the table set, the easier the agent is to validate. Start small, then add more tables later only if needed.

---

## Step 5 — Add Clear Agent Instructions

The Data Agent needs instructions so it knows how to behave and what scope to stay within.

1. Find the **Instructions** area in the Data Agent configuration.
2. Add a short, explicit prompt that covers these points:
   - What business domain the agent serves.
   - That it must answer only from the approved attached data.
   - That it must not guess if data is missing.
   - That it should respond in clear business language.
   - That it must stay within scope.

### Starter instruction example

> You are a business analytics agent for curated sales and customer support reporting. Use only the approved Gold data sources attached to this agent. If data is missing, incomplete, or unclear, say so instead of guessing. Answer in clear business language and stay within the approved analytics scope.

> **Why this matters:** Good source selection limits what the agent can access. Good instructions limit how the agent interprets and presents that data.

---

## Step 6 — Add Example Questions

If your setup supports example questions, add them now. These help users and also give you a repeatable test set.

### Good first examples

- What were total sales by month?
- Which product categories generated the most revenue?
- Which customers have the highest lifetime value?
- What support trends need attention?

### How to use them

1. Add the example questions in the Data Agent configuration.
2. Save them.
3. Use the same questions later during validation in Fabric, Foundry, and the app.

> **Best practice:** Keep 5–10 questions with known expected answers. This becomes your regression test set.

---

## Step 7 — Test the Data Agent Inside Fabric First

Do **not** connect Foundry or the app yet. Validate the agent directly inside Fabric first.

1. Open the Data Agent test experience.
2. Ask one known business question.
3. Compare the answer to the actual result from the Gold source:
   - query the Gold table directly, or
   - compare to the semantic model/report value
4. Repeat this for at least **five test questions**.
5. Record which questions passed and which did not.
6. If answers are weak or incorrect:
   - adjust the selected tables,
   - improve the instructions,
   - remove noisy or unnecessary sources,
   - test again.

### What success looks like

- The Data Agent answers in the right business domain.
- The answer matches validated source data.
- The answer does not drift outside the attached data.
- The agent says it does not know when the data is missing.

---

## Step 8 — Publish Only After Validation

Once the Data Agent behaves correctly in Fabric, publish it.

1. Save your changes.
2. Click **Publish**.
3. Record the following values for later integration:
   - **Fabric workspace ID**
   - **Data Agent artifact ID**
4. Store those values somewhere safe for the Foundry integration step.

> Use draft mode while tuning. Publish only when the Data Agent is stable enough for downstream use.

---

## Step 9 — Connect the Data Agent to Azure AI Foundry

After Fabric-side validation is complete, connect the Data Agent into Foundry.

1. Open your **Azure AI Foundry project**.
2. Create a new **Microsoft Fabric connection**.
3. When prompted, enter the required identifiers:
   - Fabric workspace ID
   - Data Agent artifact ID
4. Give the connection a clear name such as `fabric-sales-agent-connection`.
5. Save the connection.
6. Make the connection available to the correct project scope.

In Foundry, this Data Agent becomes a knowledge or tool resource that your main agent can call.

---

## Step 10 — Create or Update the Foundry Agent

Now update the Foundry agent that your app uses.

1. Open the Foundry agent used by the app.
2. Enable the **Fabric connection/tool** you created in Step 9.
3. Add instructions that clearly explain when the Foundry agent should use the Fabric Data Agent.

### Suggested instruction pattern

- Use the Fabric tool for curated business analytics questions.
- Prefer the Fabric tool for sales, customer, and support analytics.
- If the Fabric tool does not return enough information, say so clearly.
- Do not fabricate answers outside the attached business data.

> **Why this matters:** Without explicit tool-usage instructions, the Foundry agent may answer from its base model instead of calling the Fabric Data Agent when it should.

---

## Step 11 — Validate in Foundry Before Using the App

Run the same test set again, but this time through the Foundry agent.

1. Ask the same 5–10 validation questions you used in Fabric.
2. For each question, confirm all of these:
   - The Foundry agent actually calls the Fabric tool.
   - The answer matches the Fabric Data Agent output.
   - The answer matches the validated Gold data result.
   - No authentication or connection errors occur.
3. Fix any failures before moving on.

> Do not connect the app until this step passes. If Foundry is not reliably using the Fabric Data Agent here, the app will not be reliable either.

---

## Step 12 — Connect the App Runtime

After Foundry works correctly, point the app at the Foundry-based path.

1. Open your app configuration.
2. Set these runtime values:

   ```env
   CHAT_BACKEND_MODE=foundry
   USE_FOUNDRY_AGENTS=true
   FOUNDARY_PROJECT_ENDPOINT=<your endpoint>
   FABRIC_PROJECT_CONNECTION_NAME=<your Fabric connection name>
   MODEL_DEPLOYMENT_NAME=<your model deployment, if required>
   ```

3. Save the configuration.
4. Restart the app.
5. Open the app and confirm it loads normally.

> **Important:** Check the exact variable names used by your app. Some implementations use different naming conventions. Match your app's config, not just the example above.

---

## Step 13 — Prove the App Is Using the Data Agent Path

Run at least one of these tests so you can prove the app is using the Fabric Data Agent path.

### Test A — Known Answer Comparison

1. Ask a previously validated analytics question in the app.
2. Compare the app answer to the Foundry answer.
3. Compare both to the validated Gold source result.
4. Confirm all three match.

### Test B — Controlled Source Change

1. Update a known source value in Azure SQL or in the Fabric Gold path.
2. Run the required refresh flow.
3. Confirm the Data Agent answer changes inside Fabric.
4. Confirm the Foundry answer changes.
5. Confirm the app answer changes.

### Test C — Fabric-Only Question

1. Ask a question that depends on a Gold table or semantic model not available in the old SQL-only route.
2. Confirm the app answers it correctly.
3. If it can answer that question correctly, it is strong evidence the app is using the Fabric Data Agent path.

---

## Step 14 — Final Go-Live Checklist

Before calling this deployment complete, verify every item below.

- [ ] Data Agent works correctly in Fabric.
- [ ] Only approved sources and tables are exposed.
- [ ] Instructions are present and clear.
- [ ] Example questions are added and tested.
- [ ] Data Agent is published.
- [ ] Foundry connection works.
- [ ] Foundry agent works correctly.
- [ ] App runtime settings are correct.
- [ ] App answers match validated Fabric data.
- [ ] Solution documentation only claims support after validation is complete.

---

## Recommended Rollout Order

Use this rollout order in a new environment:

1. Validate the semantic model or Gold source.
2. Validate the Fabric Data Agent.
3. Publish the Data Agent.
4. Validate the Foundry connection.
5. Validate the Foundry agent.
6. Validate the app.
7. Promote to production.

---

## Troubleshooting Quick Reference

| Symptom | Likely Cause | What to Check |
|---|---|---|
| Fabric Data Agent option is missing | Tenant setting disabled or capacity not eligible | Check capacity level and tenant settings |
| Agent gives weak or irrelevant answers | Too many tables, poor instructions, or wrong source | Reduce scope and improve instructions |
| Semantic model cannot be added | Permission issue | Confirm required read/write permissions on the semantic model |
| Foundry agent does not call the Fabric tool | Tool-use instructions are missing or weak | Update Foundry instructions and re-test |
| App answers do not match Fabric answers | App still using old backend path or wrong connection | Re-check runtime settings and connection name |
| Controlled source changes do not appear | Refresh flow incomplete | Verify SQL-to-Fabric refresh path completed successfully |
