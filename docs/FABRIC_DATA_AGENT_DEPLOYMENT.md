# Fabric Data Agent and Foundry app setup

## Scope

This doc describes the optional conversational analytics path using Microsoft Fabric Data Agent plus Azure AI Foundry integration. This path should remain optional and should only be claimed in the repo after end-to-end validation succeeds.

## Prerequisites

- A paid Fabric capacity of F2 or higher.
- Fabric data agent tenant setting enabled.
- Copilot tenant switch enabled where required.
- Cross-geo processing for AI enabled.
- Cross-geo storing for AI enabled.
- A curated Fabric data source such as a lakehouse, warehouse, semantic model, or KQL database.

## Recommended data source strategy

Use curated Gold data only. Do not expose broad Bronze or Silver datasets to the data agent unless there is a strong reason.

Recommended source types for this solution:

- Gold Lakehouse tables.
- Gold Warehouse tables.
- Approved semantic models.
- KQL database for RTI-aligned scenarios if needed.

## Gold-table curation rules

Only include tables that are:

- business-facing,
- stable,
- well-described,
- low-noise,
- appropriate for question answering.

Good examples for this solution:

- `gold_customer360`
- `gold_productperformance`
- `goldsalesbycategory`
- `goldsalestimeseries`
- `goldsupportmetrics`

Avoid exposing raw or highly technical tables unless the target users truly need them.

## Fabric Data Agent setup

1. Create the Fabric Data Agent in the target Fabric workspace.
2. Add the curated Gold source.
3. Select only approved tables.
4. Add clear agent instructions that explain what the source contains and what kinds of questions it should answer.
5. Add example queries where supported.
6. Test and refine the Data Agent in Fabric.
7. Publish the Data Agent only after validation.

## Foundry integration guidance

After the Fabric Data Agent works inside Fabric, connect it to the Foundry project path used by the app.

Recommended sequence:

1. Create or confirm the Foundry project.
2. Create the Microsoft Fabric connection in the Foundry project.
3. Create or update the Foundry agent to use the Fabric tool/connection.
4. Validate the Foundry agent directly before app integration.
5. Configure the app runtime for `CHAT_BACKEND_MODE=foundry`.
6. Validate the app end to end.

## App validation path

Validation should happen in this order:

1. Fabric Data Agent answers correctly in Fabric.
2. Foundry agent answers correctly using the Fabric connection.
3. The application answers correctly through the Foundry-backed route.

Do not describe the app as fully associated with Fabric Data Agents until all three validations pass.

## ALM and source control

Fabric Data Agent ALM should be treated as part of the broader Fabric promotion strategy.

Recommended practices:

- Use Git integration for version tracking.
- Use deployment pipelines for Dev/Test/Prod promotion.
- Keep Data Agent changes in draft until validated.
- Do not directly edit published folder content in Git.

## Publish guidance

Publishing matters because published data agents are the versions available across supported consumption channels. Development work should stay in restricted development workspaces, while end users should consume agents published from production workspaces.

## Repo merge notes

- Create or update `docs/FABRIC_DATA_AGENT_FOUNDRY_APP_SETUP.md` from this file.
- Keep this path optional in README, QUICK_START, and architecture docs.
- Only claim support after end-to-end validation is complete.
