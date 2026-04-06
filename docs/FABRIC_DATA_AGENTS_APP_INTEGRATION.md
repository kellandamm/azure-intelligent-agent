# Fabric Data Agents — Setup and App Integration Guide

This guide explains how to create Microsoft Fabric Data Agents, expose the right data sources to them, connect them to Azure AI Foundry, and attach them to the app so Fabric-backed chat works end to end.[web:271][web:278]

## Goal

At the end of this setup, the app can send user questions to a Foundry agent that has access to a Microsoft Fabric Data Agent connection, allowing the app to answer questions over Fabric-hosted data with identity-aware access patterns.[web:272][web:278]

## Architecture

```text
Fabric Gold tables / Semantic Model
        |
        v
Fabric Data Agent
        |
        v
Azure AI Foundry Project Connection
        |
        v
Foundry Agent with Fabric tool
        |
        v
App chat endpoint
```

Fabric Data Agents are created in Fabric, configured with data sources and table exposure, then consumed through a Foundry connection and tool configuration.[web:271][web:273][web:278]

## Prerequisites

1. A Fabric workspace with the Gold Lakehouse or Warehouse already populated.
2. A semantic model or lakehouse tables that represent the curated demo outputs.
3. An Azure AI Foundry project with a valid project endpoint.
4. App configuration access so environment variables can be updated.
5. `USE_FOUNDRY_AGENTS=true` enabled in the app when Foundry-backed chat is desired.

The existing app already uses Foundry-style configuration such as `PROJECT_ENDPOINT` and a Fabric tool path, so this guide extends that pattern rather than introducing a new architecture.[web:273]

## Part 1: Create the Fabric Data Agent

### Step 1: Open Fabric workspace

1. Open the target Fabric workspace.
2. Confirm the Gold layer or semantic model is present.
3. Confirm you can see the tables the agent should answer over.[web:271][web:272]

### Step 2: Create a Fabric Data Agent

1. In the Fabric workspace, select **+ New item**.
2. Search for **Fabric data agent**.
3. Select it.
4. Enter a name such as `SalesDemoDataAgent`.
5. Select **Create**.[web:271]

### Step 3: Add data sources to the Data Agent

1. In the Data Agent, choose **Add data source**.
2. Select the target source type, usually one of:
- Lakehouse
- Warehouse
- Semantic model
- KQL database [web:272]
3. Choose the Gold Lakehouse or semantic model created for the demo.
4. Add the source.

Fabric Data Agents can evaluate across supported Fabric data sources and use source schema plus agent instructions to determine the best source for a question.[web:272]

### Step 4: Select tables the agent can use

1. In the left explorer pane, expand the data source.
2. Select only the tables you want exposed.
3. For this demo, prefer Gold outputs such as:
- `gold_customer_360`
- `gold_product_performance`
- `gold_sales_by_category`
- `gold_sales_time_series`
- `gold_geographic_sales`
- `gold_sales_pipeline`
- `gold_customer_rfm`
- `gold_support_metrics` [file:236]
4. Save the agent.

### Step 5: Add Data Agent instructions

Use concise instructions so the Fabric Data Agent stays scoped to the right business area.

Suggested instructions:

- Answer questions using Gold demo tables only.
- Prefer customer, sales, support, and pipeline summaries from Gold outputs.
- Do not use Bronze raw tables for business answers.
- When multiple Gold tables are possible, choose the one with the clearest business meaning.
- If a question asks for trends, prefer time-series tables.

Fabric guidance recommends using clear source selection and instructions so the agent can route questions to the correct data source.[web:272]

### Step 6: Test the Fabric Data Agent in Fabric

1. Ask a few test questions in the Fabric Data Agent UI.
2. Example prompts:
- Which states have the highest revenue?
- Show pipeline value by stage.
- Which customer segment has the highest lifetime value?
3. Confirm the agent returns sensible answers.
4. Adjust source selection or instructions if needed.[web:271]

## Part 2: Connect Fabric Data Agent to Azure AI Foundry

### Step 7: Create or verify a Fabric connection in Foundry

1. Open the Azure AI Foundry project.
2. Go to **Connections**.
3. Create or verify a **Microsoft Fabric** connection.
4. Ensure the connection can access the target Fabric workspace and Data Agent.

Foundry uses a Fabric connection ID that is referenced by the Fabric tool when building an agent.[web:273][web:278]

### Step 8: Record the connection details

Capture these values:

- Foundry project endpoint.
- Fabric connection name.
- Fabric connection ID.
- Model deployment name.

The connection ID is typically in the form:

```text
/subscriptions/<subscription-id>/resourceGroups/<resource-group>/providers/Microsoft.MachineLearningServices/workspaces/<project-name>/connections/<fabric-connection-name>
```

This connection ID is used by the Foundry Fabric tool configuration.[web:273]

### Step 9: Create a Foundry agent that uses the Fabric tool

Use a Fabric-aware tool definition in the Foundry project. Microsoft documents using the Microsoft Fabric tool in Foundry Agent Service with a project connection reference.[web:278]

Python example pattern:

```python
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    PromptAgentDefinition,
    MicrosoftFabricPreviewTool,
    FabricDataAgentToolParameters,
    ToolProjectConnection,
)

project_client = AIProjectClient(
    endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
    credential=DefaultAzureCredential(),
)

fabric_connection = project_client.connections.get(
    os.environ["FABRIC_PROJECT_CONNECTION_NAME"]
)

agent = project_client.agents.create_version(
    agent_name="FabricSalesAgent",
    definition=PromptAgentDefinition(
        model=os.environ["FOUNDRY_MODEL_DEPLOYMENT_NAME"],
        instructions="You answer questions about demo sales, pipeline, support, and customer analytics.",
        tools=[
            MicrosoftFabricPreviewTool(
                fabric_dataagent_preview=FabricDataAgentToolParameters(
                    project_connections=[
                        ToolProjectConnection(
                            project_connection_id=fabric_connection.id
                        )
                    ]
                )
            )
        ],
    ),
)
```

This is the documented Foundry pattern for connecting a Fabric Data Agent through a project connection.[web:278]

## Part 3: Attach the Data Agent to the app

### Step 10: Update app configuration

Set these app settings or environment variables:

- `USE_FOUNDRY_AGENTS=true`
- `PROJECT_ENDPOINT=<your foundry project endpoint>`
- `FOUNDRY_PROJECT_ENDPOINT=<your foundry project endpoint>` if your implementation uses this name
- `FOUNDRY_MODEL_DEPLOYMENT_NAME=<your model deployment>`
- `FABRIC_PROJECT_CONNECTION_NAME=<your fabric connection name>`
- Any existing OpenAI deployment settings the app already needs

The repo’s earlier behavior indicates Foundry-backed chat depends on project endpoint configuration, so these settings need to be valid before Fabric chat can succeed.[web:273]

### Step 11: Update the app agent manager

The app’s Foundry agent manager should do the following when Fabric mode is enabled:

1. Read the Foundry project endpoint.
2. Read the Fabric connection name.
3. Resolve the Fabric connection from the Foundry project.
4. Create or reuse a Foundry agent with the Fabric tool attached.
5. Route chat requests through that agent.

If your app still uses the older `FabricTool(connection_id=...)` shape, update the implementation to the current Foundry Microsoft Fabric tool pattern if needed, because current documentation shows `MicrosoftFabricPreviewTool` with `ToolProjectConnection` references.[web:273][web:278]

### Step 12: Recommended app-side mode toggle

Add a clear mode concept in the app:

- `SQL` mode = synthetic Azure SQL path, no Fabric Data Agent.
- `Fabric` mode = Foundry agent with Fabric Data Agent connection enabled.

When Fabric mode is on:

- Show `Fabric Data Agent connected` in admin UI.
- Show workspace or connection name.
- Show last successful Fabric chat test.

When SQL mode is on:

- Hide Fabric Data Agent status controls.

## Part 4: Validate end-to-end

### Step 13: Test directly in Foundry

Send a prompt through the Foundry agent first, before testing in the app.

Example prompts:

- What are the top revenue categories?
- Show sales by geography.
- Which pipeline stage has the most weighted value?

If this fails in Foundry, the app will fail too.[web:278]

### Step 14: Test in the app

1. Restart the app after updating settings.
2. Open the chat UI.
3. Ask one Gold-table question.
4. Confirm the response returns successfully.
5. Try a second question that should route to a different Gold output.

## Recommended troubleshooting section

### If the app returns HTTP 500

Check these first:

- `USE_FOUNDRY_AGENTS` is actually enabled.
- `PROJECT_ENDPOINT` or `FOUNDRY_PROJECT_ENDPOINT` is valid.
- The Fabric project connection name is correct.
- The Foundry agent was created successfully.
- The Fabric Data Agent can answer the same question inside Fabric.
- The app identity has permission to use the Foundry project and Fabric connection.

A bad Foundry project endpoint, missing connection, or failed agent initialization will surface as app chat failures because the Fabric-enabled path depends on Foundry agent creation and invocation.[web:273][web:278]

### If the Data Agent gives weak answers

- Remove noisy or irrelevant tables.
- Keep the scope primarily Gold.
- Tighten the instructions.
- Prefer semantic-model-backed curated data when available.

### If the connection exists but queries fail

- Recheck user permissions in Fabric.
- Recheck workspace access.
- Recheck whether the Data Agent was saved after selecting tables.

## Suggested repo documentation structure

Add a new document such as:

- `docs/FABRIC_DATA_AGENTS.md`

It should include:

1. How to create the Fabric Data Agent.
2. Which Gold tables to expose.
3. How to connect it in Foundry.
4. Which app settings must be added.
5. How to test in Foundry and then in the app.
6. Troubleshooting for 500 errors and connection failures.

## Copy-ready short insert

> Fabric chat in this app uses a Microsoft Fabric Data Agent connected through Azure AI Foundry. Create the Fabric Data Agent in the Fabric workspace, expose only the Gold demo tables, create a Microsoft Fabric connection in Foundry, and configure the app to use the Foundry project endpoint plus Fabric connection settings. Test in Fabric first, then Foundry, then the app.
