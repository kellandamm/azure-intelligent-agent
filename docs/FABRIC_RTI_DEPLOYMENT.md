# RTI Deployment — Fabric Real-Time Intelligence Setup Guide

This guide walks you through deploying **Fabric Real-Time Intelligence (RTI)** from scratch and verifying that your app or operations reports are using the real-time data path. Follow every step in order — each builds on the previous one.

---

## What You Are Building

You are setting up a real-time event pipeline using these Fabric components:

| Component | What It Does |
|---|---|
| **Eventstream** | Captures and routes live events from a source (e.g., database changes) |
| **Eventhouse** | Stores and queries the incoming events (operational analytics store) |
| **Activator** | Monitors the event stream and fires alerts or actions when rules are met |

**The full data flow looks like this:**

```
Azure SQL Database CDC → Eventstream → Eventhouse → Activator → Alert / Dashboard
```

---

## Before You Start

Gather the following before touching anything in Fabric:

- [ ] Access to a **Fabric workspace** on Fabric capacity or trial (not a free workspace)
- [ ] **Contributor role or higher** in that workspace
- [ ] A real event source ready — one of:
  - Azure SQL Database with CDC enabled (most common for this solution)
  - Azure Event Hubs
  - A custom application emitting events
- [ ] A clear first **business scenario** to monitor. Pick one:
  - Support ticket surge
  - Order anomaly or threshold breach
  - KPI threshold breach
  - Customer health score deterioration

> **Start with one scenario.** Do not try to monitor multiple event types until the first end-to-end path is fully working.

---

## Step 1 — Prepare the Source System (Azure SQL CDC)

> Skip this step if your source is Event Hubs or a custom app — go to Step 2.

If your event source is **Azure SQL Database Change Data Capture (CDC)**, you need to enable CDC before Eventstream can connect to it.

1. Open the **Azure portal** and navigate to your **Azure SQL Database**.
2. Open **Query editor** (in the left menu) or connect via SQL Server Management Studio (SSMS).
3. Run the following SQL to enable CDC at the **database level**:

   ```sql
   EXEC sys.sp_cdc_enable_db;
   ```

4. Enable CDC on each **table** you want to monitor. Replace `dbo` and `YourTableName` with your schema and table name:

   ```sql
   EXEC sys.sp_cdc_enable_table
       @source_schema = N'dbo',
       @source_name   = N'YourTableName',
       @role_name     = NULL;
   ```

   Repeat for each table you want to stream.

5. Confirm CDC is active by querying:

   ```sql
   SELECT name, is_cdc_enabled FROM sys.databases WHERE name = DB_NAME();
   ```

   The result should show `is_cdc_enabled = 1`.

> **Important network requirement:** Fabric Eventstream's Azure SQL CDC connector requires your Azure SQL database to be **publicly accessible**. It cannot connect through a private endpoint or VNet-restricted firewall. If your database is locked down, you will need to temporarily open access or use a different source type.

> **Authentication:** Eventstream currently only supports **Basic authentication** (SQL username + password) for this connector — not Azure AD or managed identity.

---

## Step 2 — Create the Eventstream

The Eventstream is the entry point for your real-time data. Think of it as a pipeline that receives raw events and routes them to destinations.

1. Open your **Fabric workspace**.
2. Click **+ New item** (top of the workspace view).
3. Search for and select **Eventstream**.
4. Give it a descriptive name such as `Operations_RTI_Stream`.
5. Click **Create**.
6. The Eventstream editor will open. You are now in **Edit mode** — changes here are drafts until you publish.

---

## Step 3 — Add Your Event Source

### Option A — Azure SQL Database CDC (Recommended)

1. In the Eventstream editor, click **Add source** (left side of the canvas).
2. Select **Azure SQL Database CDC** from the source list.
3. Fill in the connection details:
   - **Connection name**: Give it a readable label (e.g., `AzureSQL_Operations`)
   - **Server**: Your Azure SQL server address (e.g., `yourserver.database.windows.net`)
   - **Database**: Your database name
   - **Username / Password**: SQL authentication credentials
4. Once connected, select the **tables** you want to monitor (the ones you enabled CDC on in Step 1).
5. Click **Save**.

> You should see the source appear as a node on the Eventstream canvas.

### Option B — Other Source Types

If you are not using Azure SQL CDC, supported alternatives include:

- **Azure Event Hubs** — for pre-existing event hub streams
- **Custom app source** — for apps that push events directly
- **Workspace item events** — for Fabric-internal event triggers

The setup flow is similar: click **Add source**, choose your type, and fill in the connection details.

---

## Step 4 — Add Transformations (If Needed)

Before routing events to a destination, you can shape the data. Keep this minimal on the first pass.

1. In the Eventstream editor, click the **+** button on the stream between your source and destination to insert a transformation.
2. Common first transformations to consider:

   | Transformation | When to Use |
   |---|---|
   | **Filter** | You only want events from one specific table or operation type (e.g., only INSERTs) |
   | **Select** | You want to drop unnecessary columns and keep only the fields your reports need |
   | **Flatten** | CDC events wrap change data in nested JSON — use this to surface individual column values |
   | **Manage fields** | Rename columns or cast data types |

3. After adding a transformation, click **Preview** to confirm the output looks correct before moving on.

> **Best practice:** If you are unsure what shape you need, skip transformations for now and add them after Step 9 (validation). A working simple pipeline is better than a broken complex one.

---

## Step 5 — Add Eventhouse as a Destination

Eventhouse stores your event data so you can query it, build dashboards, and analyze trends over time.

1. In the Eventstream editor, click **Add destination**.
2. Select **Eventhouse** from the destination list.
3. Configure the destination:
   - **Workspace**: Select your Fabric workspace
   - **Eventhouse**: Either select an existing one or create a new one (click **Create new Eventhouse** if this is your first time)
   - **KQL Database**: Select or create a database inside the Eventhouse
   - **Table**: Enter a table name where events will land (e.g., `operations_events`)
4. Click **Save**.
5. Click **Publish** (top right of the editor) to activate the Eventstream.

> After publishing, switch to **Live view** (toggle at the top of the editor). You should see the Eventhouse destination listed and a status indicator. Wait 1–2 minutes for the first events to flow through.

---

## Step 6 — Add Activator as a Destination

Activator is the alerting engine. It watches the event stream and triggers actions when your defined conditions are met.

1. In the Eventstream editor, click **Add destination** again (you can have multiple destinations).
2. Select **Activator**.
3. Configure it:
   - **Destination name**: e.g., `Operations_Activator`
   - **Workspace**: Select your workspace
   - **Activator**: Select an existing Activator item or click **Create new**
4. Click **Save**.
5. Click **Publish** again.

> After publishing, the Activator destination will appear in Live view. You will configure the actual alert rules inside Activator in Steps 9–11.

---

## Step 7 — Validate That Events Are Flowing

**Do not proceed to alert rules until you confirm data is actually moving through the pipeline.** This is the most important checkpoint.

1. In the Eventstream **Live view**, check the source node — you should see an event count incrementing.
2. Click the stream between the source and Eventhouse destination — confirm event counts are non-zero.
3. Open your **Eventhouse** in the Fabric workspace, then open the **KQL Database**.
4. Run a quick query to confirm rows are landing:

   ```kql
   operations_events
   | take 10
   ```

   Replace `operations_events` with whatever table name you set in Step 5.

5. Review the results:
   - Are timestamps current (within the last few minutes)?
   - Are the key business fields (order ID, customer ID, ticket ID, etc.) present and populated?
   - Does the operation type field (e.g., INSERT, UPDATE) look correct?

> **If you see zero rows or the query errors:** Stop here. Do not proceed to Activator rules. Diagnose the source connection or transformation before moving on. Common issues: CDC not enabled, firewall blocking Eventstream, wrong table name in destination.

---

## Step 8 — Create the Activator Object

An Activator **object** represents the business entity you are monitoring (e.g., a support ticket, an order, a customer). You define what uniquely identifies each one.

1. Open **Activator** from your Fabric workspace (find it in the workspace item list, or open it from the Eventstream Live view).
2. Open the incoming stream connected from your Eventstream.
3. Click **New object**.
4. Configure the object:
   - **Object name**: Use the business entity name (e.g., `SupportTicket`, `Order`, `Customer`)
   - **Unique ID field**: Choose the column that uniquely identifies each entity — for example:
     - `ticket_id` for support events
     - `order_id` for order events
     - `customer_id` for customer health events
5. Add the **properties** you want to track — these are the column values Activator will monitor for changes (e.g., `status`, `priority`, `order_total`, `health_score`).
6. Click **Save**.

---

## Step 9 — Create the First Alert Rule

Keep your first rule simple and easy to verify. You want something that will definitely fire during testing.

1. Inside Activator, select the object you just created.
2. Click **New rule**.
3. Define the condition. Examples by scenario:

   | Scenario | Condition Example |
   |---|---|
   | Support ticket surge | `ticket count > 10 in the last 5 minutes` |
   | Order anomaly | `order_total > 5000` |
   | Customer health | `health_score < 40` |
   | Delivery delay | `delay_minutes > 30` |

4. Set the **evaluation frequency** — how often Activator checks the condition (e.g., every 1 minute).
5. Do NOT enable the action yet — first click **Test** (or **Preview**) to simulate the rule against recent data.
6. Confirm the rule would fire for the right events and not for the wrong ones.

---

## Step 10 — Configure the Alert Action

Once the rule is validated, set up what happens when it fires.

1. Still inside the rule editor, click **Add action**.
2. Choose an action type:

   | Action | Best For |
   |---|---|
   | **Email** | Async notifications to individuals |
   | **Teams message** | Team-wide operational alerts |
   | **Power Automate flow** | Triggering downstream workflows or ticketing systems |
   | **Fabric item action** | Triggering a Fabric pipeline or notebook |

3. Configure the action with the appropriate recipient, channel, or flow.
4. **Test the action** before enabling it:
   - Use the **Test action** button to send a test notification.
   - Confirm the email arrives, Teams message appears, or flow triggers.
5. Enable the rule.

> **Why test first?** Misconfigured actions (wrong email address, wrong Teams channel) are silent failures — the rule fires but nothing happens. Always confirm receipt before calling it done.

---

## Step 11 — Build a Validation Dashboard or Query View

An alert is not a complete RTI solution on its own. Build a basic operational view so the team can see what is happening in real time.

1. In your **Eventhouse KQL Database**, open the query editor.
2. Create and save these starter queries:

   **Event volume by minute:**
   ```kql
   operations_events
   | summarize EventCount = count() by bin(timestamp, 1m)
   | render timechart
   ```

   **Current alert count:**
   ```kql
   operations_events
   | where timestamp > ago(1h)
   | summarize AlertCount = count()
   ```

   **Top affected entities (last hour):**
   ```kql
   operations_events
   | where timestamp > ago(1h)
   | summarize Count = count() by entity_id
   | top 10 by Count desc
   ```

3. Optionally, click **Pin to dashboard** on each query result to build a **Real-Time Dashboard** in Fabric.
4. Save the dashboard as `Operations_RTI_Dashboard`.

> This dashboard gives the operations team visibility without needing to query directly — and lets you verify that data is flowing correctly at a glance.

---

## Step 12 — End-to-End Controlled Test

Run a single controlled test to prove the entire pipeline works together.

1. In your Azure SQL source, **insert or update a known test record** — for example, add a support ticket with a distinctive ID like `TEST-9999`.
2. Wait 30–60 seconds for CDC to capture the change and Eventstream to process it.
3. In Eventstream Live view — confirm the test event appears in the stream.
4. In Eventhouse — query for the test record:
   ```kql
   operations_events
   | where ticket_id == "TEST-9999"
   ```
   Confirm it appears.
5. In Activator — confirm the rule evaluated the test event (check the rule activity log).
6. Confirm the alert action fired (check email inbox, Teams channel, or flow run history).
7. If you built a dashboard in Step 11, refresh it — confirm the test event appears there too.

**All six checkpoints must pass before this step is complete.**

---

## Step 13 — Prove the App Is Using the RTI Output

Run at least one of these tests to confirm your app or operational layer is reading from the RTI path — not a stale batch source.

### Test A — Alert Path Test

1. Trigger a condition that matches your Activator rule.
2. Confirm the alert appears in the expected channel (email, Teams, etc.).
3. Confirm the app or dashboard reflects the same event state.

### Test B — Eventhouse Direct Comparison

1. Query Eventhouse directly for a metric (e.g., event count in the last hour).
2. Compare that value to what the app or operational dashboard shows.
3. They should match — if they don't, the app may still be pulling from a batch source.

### Test C — End-to-End Timestamp Trace

1. Insert a known event in the source system and note the exact time.
2. Track the event through each layer:
   - Eventstream ingestion timestamp
   - Eventhouse arrival timestamp
   - Activator evaluation timestamp
   - App or dashboard display timestamp
3. Confirm the IDs and values stay consistent through every layer and that the end-to-end latency is within your expected range.

---

## Step 14 — Final Go-Live Checklist

Before declaring RTI complete, verify every item:

- [ ] Azure SQL CDC is enabled on all required tables (or alternative source is confirmed active)
- [ ] Eventstream source is connected and receiving events
- [ ] Transformations produce the correct output shape (verified via Preview)
- [ ] Eventhouse is receiving rows with correct timestamps and field values
- [ ] Activator object is created with the correct unique ID field
- [ ] At least one alert rule is defined, tested, and enabled
- [ ] At least one action is configured and confirmed delivered during testing
- [ ] Validation dashboard or query view is built and loads current data
- [ ] End-to-end controlled test passed all six checkpoints (Step 12)
- [ ] App or operational layer confirmed reading from RTI output (Step 13)
- [ ] Team knows which source path, rules, and actions are in production

---

## Recommended Production Rollout Order

Follow this sequence when promoting to production:

1. ✅ Validate the source system (CDC active, data is flowing)
2. ✅ Validate Eventstream (events arriving, transformations correct)
3. ✅ Validate Eventhouse (rows landing, queries return expected data)
4. ✅ Validate Activator object and first rule (fires on correct conditions)
5. ✅ Validate action delivery (alert actually received)
6. ✅ Validate dashboard or app consumption (values match Eventhouse)
7. 🚀 Promote to production — update any non-production settings to production endpoints

---

## Troubleshooting Quick Reference

| Symptom | Likely Cause | What to Try |
|---|---|---|
| Eventstream shows zero events | CDC not enabled, firewall blocking, wrong credentials | Re-check Step 1; verify Azure SQL is publicly accessible |
| Eventhouse table is empty | Eventstream not published, wrong table name, destination misconfigured | Re-publish Eventstream; check destination settings in Step 5 |
| Activator rule never fires | Rule condition too strict, wrong property mapped, object ID wrong | Simplify the condition; preview against recent data |
| Alert action not received | Wrong email/channel, action not saved, rule not enabled | Use Test action button; confirm rule is enabled |
| Timestamps are wrong or missing | CDC payload not flattened, wrong field mapped | Add a Flatten transformation; check timestamp field name |
| App shows stale data | App not connected to RTI output, old batch source still in use | Re-run Test B or C from Step 13 to confirm the data path |
