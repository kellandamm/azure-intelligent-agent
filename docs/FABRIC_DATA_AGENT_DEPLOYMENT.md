# Data Agent Deployment — Step by Step

Use these steps to deploy a Fabric Data Agent and prove that it is using the curated Fabric data path you expect.

## Step 1 — Confirm prerequisites

Before creating the Data Agent, confirm all of these:

- Fabric capacity is paid F2 or higher.
- Fabric Data Agent tenant setting is enabled.
- Copilot tenant setting is enabled where required.
- Cross-geo processing for AI is enabled if your tenant requires it.
- Cross-geo storing for AI is enabled if your tenant requires it.
- Your Fabric workspace already contains the curated data source you want the Data Agent to use.

Supported source types include:

- Lakehouse.
- Warehouse.
- Power BI semantic model.
- KQL database.

## Step 2 — Decide what source to expose

Use curated business-facing data only.

Recommended first source choice:

1. Gold semantic model, if it is already validated.
2. Gold Lakehouse tables, if the semantic model is not ready.
3. Gold Warehouse tables, if that is your governed analytics path.

Avoid using Bronze or Silver data for the first production Data Agent.

## Step 3 — Create the Fabric Data Agent

1. Go to your Fabric workspace.
2. Select **+ New item**.
3. Search for **Fabric data agent**.
4. Enter a clear name such as `Sales Insights Agent` or `Customer Analytics Agent`.
5. Create the item.

After creation, the OneLake catalog opens so you can add data sources.

## Step 4 — Add the data source

1. In the OneLake catalog, select the validated source.
2. Click **Add**.
3. Repeat only if you truly need more than one source.

Important guidance:

- Keep the first version narrow.
- Fabric Data Agent supports up to five sources, but the first deployment should usually use one trusted source.
- If you use a semantic model, make sure you have the required read/write permissions to add it.

## Step 5 — Select only the approved tables

After adding the source:

1. Open the source in the left Explorer pane.
2. Review the available tables.
3. Select only the tables the agent should answer questions about.

Recommended first-table set:

- `gold_customer360`
- `gold_productperformance`
- `goldsalesbycategory`
- `goldsalestimeseries`
- `goldsupportmetrics`

Keep the first version focused. A smaller table set is easier to validate and trust.

## Step 6 — Add instructions

Write short, explicit instructions inside the Data Agent.

Suggested pattern:

1. Explain what business domain the agent covers.
2. Tell it to answer only from the selected data.
3. Tell it to avoid guessing when data is missing.
4. Tell it to summarize clearly and use business language.
5. Tell it not to answer outside its data scope.

Example instruction starter:

> You are a business analytics agent for curated sales and customer support reporting. Use only the approved Gold data sources attached to this agent. If the data is missing or unclear, say so instead of guessing.

## Step 7 — Add example questions

Add a few known-good example questions if supported in your setup.

Good first examples:

- What were total sales by month?
- Which product categories generated the most revenue?
- Which customers have the highest lifetime value?
- What support trends need attention?

This improves usability and gives you a repeatable validation set.

## Step 8 — Test inside Fabric first

Before connecting anything to Foundry or the app:

1. Ask a known question.
2. Compare the Data Agent answer to the actual Gold table or semantic model result.
3. Repeat for at least five test questions.
4. Fix table selection or instructions if answers are weak.

Best practice:

- Build a small test set with known correct answers.
- Validate answers against direct queries to the curated source.

## Step 9 — Publish only after validation

Once the Data Agent answers correctly in Fabric:

1. Save your changes.
2. Publish the Data Agent.
3. Record the workspace ID and the Data Agent artifact ID for later integration.

Use draft mode while tuning. Publish only when the Data Agent is stable enough for downstream use.

## Step 10 — Connect the Data Agent to Foundry

After the Fabric-side validation is complete:

1. Open your Azure AI Foundry project.
2. Create a Microsoft Fabric connection to the Data Agent.
3. Use the Fabric workspace ID and Data Agent artifact ID when required.
4. Give the connection a clear name.
5. Make it available to the correct project scope.

In Foundry, the Fabric Data Agent is added as a knowledge/tool resource.

## Step 11 — Create or update the Foundry agent

1. Open the Foundry agent used by the app.
2. Enable the Fabric connection/tool.
3. Add instructions that explain when the agent should use the Fabric Data Agent.
4. Keep the instructions explicit.

Suggested pattern:

- Use the Fabric tool for curated business analytics questions.
- Prefer the Fabric tool for sales, customer, and support analytics.
- If the tool does not return enough information, say so clearly.

## Step 12 — Validate in Foundry before using the app

Run the same test questions again in Foundry.

Check all of these:

- The agent calls the Fabric tool.
- The answer matches the Fabric Data Agent output.
- The answer matches the validated Gold data result.
- No authentication or connection errors occur.

Do not move to the app until this passes.

## Step 13 — Connect the app runtime

Once Foundry works:

1. Set `CHAT_BACKEND_MODE=foundry`.
2. Set `USE_FOUNDRY_AGENTS=true`.
3. Set the Foundry project endpoint.
4. Set the Fabric project connection name.
5. Set the model deployment name if required.
6. Restart the app.

## Step 14 — Prove the app is using the Data Agent path

Use one of these tests:

### Test A — Known answer comparison

1. Ask a validated analytics question in the app.
2. Compare the answer to the Foundry result.
3. Compare both to the Gold source result.
4. Confirm they match.

### Test B — Controlled source change

1. Update a known source value in Azure SQL or the Fabric Gold path.
2. Run the required refresh flow.
3. Confirm the Data Agent answer changes in Fabric.
4. Confirm the Foundry answer changes.
5. Confirm the app answer changes.

### Test C — Fabric-only question

1. Ask a question that depends on a curated Gold table or semantic model not exposed in the old SQL-only route.
2. Confirm the app answers it correctly.

## Step 15 — Final go-live checklist

Before calling this complete, confirm:

- Data Agent works in Fabric.
- Only approved sources and tables are exposed.
- Instructions are present and clear.
- Example questions are tested.
- Data Agent is published.
- Foundry connection works.
- Foundry agent works.
- App runtime is set correctly.
- App answers match validated Fabric data.
- Repo wording claims support only after all validations pass.

## Recommended rollout order

Use this order:

1. Validate the semantic model or Gold source.
2. Validate the Fabric Data Agent.
3. Publish the Data Agent.
4. Validate the Foundry connection.
5. Validate the Foundry agent.
6. Validate the app.
7. Promote to production.
