# RTI Deployment — Step by Step

Use these steps to deploy Fabric Real-Time Intelligence and prove that the app or operations reports are using the intended real-time path.

## Step 1 — Confirm prerequisites

Before creating RTI items, confirm all of these:

- You have access to a Fabric workspace.
- The workspace is on Fabric capacity or trial with Contributor or higher access.
- You have a real event source ready, such as Azure SQL Database CDC, Event Hubs, or a custom application event source.
- You know the first business scenario you want to monitor.

Recommended first scenario:

- support-ticket surge,
- order anomaly,
- KPI threshold breach,
- customer health deterioration.

## Step 2 — Pick the first event path

Keep the first RTI flow simple.

Recommended path for this solution:

`Azure SQL Database CDC -> Eventstream -> Eventhouse -> Activator -> alert/dashboard`

This is a strong first path because Fabric Eventstream supports Azure SQL Database CDC, Eventhouse gives you the operational analysis store, and Activator closes the loop with actions.

## Step 3 — Prepare the source system

If you are using Azure SQL Database CDC:

1. Open Azure SQL Database.
2. Enable CDC at the database level.
3. Enable CDC on the required source tables.
4. Confirm the source tables contain the events you actually want to monitor.

Important note:

- Fabric Eventstream Azure SQL CDC requires the Azure SQL database to be publicly accessible and not behind a firewall or secured in a virtual network for this connector path.
- Eventstream currently supports Basic authentication for this connector.

## Step 4 — Create the Eventstream

1. Go to your Fabric workspace.
2. Select **+ New item**.
3. Create an **Eventstream**.
4. Give it a clear name such as `Operations_RTI_Stream`.
5. Open it in Edit mode.

## Step 5 — Add the source

### Option A — Azure SQL Database CDC

1. In the Eventstream, select **Add source**.
2. Choose **Azure SQL Database CDC**.
3. Enter the connection name.
4. Enter the server and database details.
5. Use the supported authentication method.
6. Select the tables to monitor.
7. Save the source.

### Option B — Other sources

You can also use:

- Azure Event Hubs,
- custom app source,
- workspace item events,
- other supported RTI sources.

## Step 6 — Add transformations if needed

Before routing events onward, add only the minimum shaping logic needed.

Common first transformations:

- filter to the target table or event type,
- select only the required fields,
- flatten CDC payload columns,
- keep metadata such as timestamp and operation type.

Best practice:

- Keep the first eventstream transformation simple and readable.
- Only add complexity after the first end-to-end path is proven.

## Step 7 — Add Eventhouse as a destination

1. In Eventstream Edit mode, select **Add destination**.
2. Choose **Eventhouse**.
3. Pick the workspace and create or choose the Eventhouse target.
4. Save the destination.
5. Publish the Eventstream.

After publishing, confirm the destination is visible in Live view.

## Step 8 — Add Activator as a destination

1. In Eventstream Edit mode, select **Add destination**.
2. Choose **Activator**.
3. Enter a destination name.
4. Select the workspace.
5. Select an existing Activator or create a new one.
6. Save the destination.
7. Publish the Eventstream.

The Activator destination becomes available in Live view after publish.

## Step 9 — Validate live event flow

Before building rules, confirm the event path is alive.

Check all of these:

1. Source events are arriving in Eventstream.
2. The transformed stream looks correct.
3. Eventhouse is receiving rows.
4. Timestamps and key business fields look correct.

If this fails, stop here and fix the source or transformation before configuring alerts.

## Step 10 — Create the Activator object

Inside Activator:

1. Open the incoming stream.
2. Create a new object based on the business entity you want to monitor.
3. Choose the unique ID field for that object.
4. Add the properties you want to track.

Examples:

- Ticket ID for support events.
- Order ID for order events.
- Customer ID for customer health events.

## Step 11 — Create the first rule

Keep the first rule simple and obvious.

Example rule ideas:

- Ticket volume above threshold in a short interval.
- Order total above anomaly threshold.
- Customer health score below threshold.
- Delivery delay above threshold.

Inside Activator:

1. Select the object.
2. Create a new rule.
3. Define the condition.
4. Choose the action.
5. Test the action before enabling it.

## Step 12 — Add the action

Common first actions:

- email alert,
- Teams notification,
- downstream workflow,
- operational follow-up task.

Best practice:

- Use a test action first.
- Confirm the action is actually received before calling the RTI path ready.

## Step 13 — Build a validation dashboard or query view

Use Eventhouse queries or a real-time dashboard to confirm that the event path is usable for operations visibility.

Recommended first checks:

- event count by minute,
- current alert count,
- top affected entities,
- latest triggered events.

This helps prove that RTI is not just firing alerts but also supporting real operational monitoring.

## Step 14 — Prove the RTI path is working end to end

Use one controlled test event.

Recommended validation sequence:

1. Insert or update a known source record.
2. Confirm the event appears in Eventstream.
3. Confirm the event lands in Eventhouse.
4. Confirm the Activator rule evaluates it.
5. Confirm the alert or action fires.
6. Confirm any dashboard or report shows the event.

If all six happen, the RTI path is working.

## Step 15 — Prove the app or operations layer is using RTI output

Use one of these tests:

### Test A — Alert path

1. Trigger the known RTI rule.
2. Confirm the alert appears in the target operational channel.
3. Confirm the app or dashboard reflects the same event state.

### Test B — Eventhouse comparison

1. Query Eventhouse directly.
2. Compare the event counts or status values with the operational view used by the app or dashboard.
3. Confirm they match.

### Test C — Controlled business event

1. Create a known source event.
2. Track it through Eventstream, Eventhouse, Activator, and the final user-facing output.
3. Confirm timestamps and IDs stay consistent.

## Step 16 — Final go-live checklist

Before calling RTI complete, confirm:

- Eventstream source works.
- Transformations are correct.
- Eventhouse receives the expected data.
- Activator object is configured correctly.
- At least one rule is tested.
- At least one action is tested.
- Dashboard or operational query view is validated.
- Controlled end-to-end test passes.
- Team knows which source path and alert rules are in production.

## Recommended rollout order

Use this order:

1. Validate the source.
2. Validate Eventstream.
3. Validate Eventhouse.
4. Validate Activator object and rule.
5. Validate action delivery.
6. Validate dashboard or app consumption.
7. Promote to production.
