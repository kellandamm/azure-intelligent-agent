# Microsoft Fabric Setup — Mirroring, Medallion Architecture & Pipelines

Sets up Microsoft Fabric to mirror your Azure SQL database and build a medallion analytics architecture that powers dashboards, curated analytics, and Data Agent scenarios.

> **No Fabric?** Skip this guide entirely. Run `app/Fabric/synthetic_data.sql` against Azure SQL and the app works without any Fabric configuration. See [QUICK_START.md Phase 6](../docs/QUICK_START.md#phase-6--fabric).

---

## Architecture Overview

```
Azure SQL DB  ──Mirror──▶  Fabric OneLake (Bronze — live replica)
                                    │
                             Notebooks / Dataflows
                                    │
                           Fabric Lakehouse Silver  (cleansed)
                                    │
                             Notebooks / Pipeline
                                    │
                           Fabric Lakehouse Gold    (analytics-ready)
                                    │
                     App AI Agents + Analytics Dashboard
                      (via Fabric SQL Analytics Endpoint)
```

**Bronze** = raw mirrored tables from Azure SQL (automatic, no code)
**Silver** = cleansed, standardised views
**Gold**   = pre-aggregated tables matching the schema expected by the app's agent tools and API routes

---

## Prerequisites

- Microsoft Fabric capacity assigned to your tenant (F2 or higher, or a Fabric trial)
- Azure SQL database deployed and seeded (Phase 2 + Phase 5 of QUICK_START.md complete)
- Azure CLI logged in with Contributor access to the resource group
- Fabric workspace admin rights
    - [ ] Add your user as Fabric Administrator in Entra if you are doing to use Fabric
---

## Phase 1 — Create a Fabric Workspace

1. Navigate to [app.fabric.microsoft.com](https://app.fabric.microsoft.com)
2. **Workspaces** (left sidebar) → **+ New workspace**
3. Name: `AgentDemo-Analytics` (or your preference)
4. **Advanced** → assign your Fabric capacity (F2+)
5. Click **Apply**

Copy the **Workspace ID** for use in Phase 5:
 copy the string after groups in the browser URL: https://app.fabric.microsoft.com/groups/59e21e68-643e-4497-8601-9asdfasdfasdf/list?experience=fabric-developer
    **WORKSPACE ID** = 59e21e68-643e-4497-8601-9asdfasdfasdf

---

## Phase 2 — Prepare Azure SQL for Mirroring

Fabric mirroring uses SQL Change Tracking to replicate rows as they change.
Run the following in **Azure Portal → SQL Database → Query Editor**
(authenticate with your Azure AD admin account):

```sql
-- Enable change tracking on the database (7-day retention)
ALTER DATABASE CURRENT
    SET CHANGE_TRACKING = ON
    (CHANGE_RETENTION = 7 DAYS, AUTO_CLEANUP = ON);

-- Enable per-table tracking on the tables you want mirrored
ALTER TABLE dbo.Categories  ENABLE CHANGE_TRACKING WITH (TRACK_COLUMNS_UPDATED = ON);
ALTER TABLE dbo.Products    ENABLE CHANGE_TRACKING WITH (TRACK_COLUMNS_UPDATED = ON);
ALTER TABLE dbo.Customers   ENABLE CHANGE_TRACKING WITH (TRACK_COLUMNS_UPDATED = ON);
ALTER TABLE dbo.Orders      ENABLE CHANGE_TRACKING WITH (TRACK_COLUMNS_UPDATED = ON);
ALTER TABLE dbo.OrderItems  ENABLE CHANGE_TRACKING WITH (TRACK_COLUMNS_UPDATED = ON);
ALTER TABLE dbo.CustomerDim ENABLE CHANGE_TRACKING WITH (TRACK_COLUMNS_UPDATED = ON);
ALTER TABLE dbo.ProductDim  ENABLE CHANGE_TRACKING WITH (TRACK_COLUMNS_UPDATED = ON);
ALTER TABLE dbo.SalesFact   ENABLE CHANGE_TRACKING WITH (TRACK_COLUMNS_UPDATED = ON);
```

> Existing gold tables (`gold_*`) do not need change tracking — they will be rebuilt by the Gold pipeline.

## Scale the Database and allow access from Fabric to database

1. Still in the Azure Portal > go to settings > Compute + storage > change Service Tier > Standard  > DTUs 100 > Click Apply. 

2. Click on SQL Logical Servers within the Azure SQL blade > Click on your SQL Server > Security > Networking > bottom of screen check the box for > Allow Azure services and resources access to this server.

3. in Fabric Workspace > click on Workspace Settings > Workspace Identity > click on +Workspace Identity and it will create an identity > take note of the name as it will be used in the command for phase 3. 

---

## Phase 3 — Create the Mirrored Database (Bronze)

1. In your Fabric workspace → **+ New item** → **Mirrored Azure SQL Database**
2. Click **+ New connection** and enter:
   - **Server**: `<your-server>.database.windows.net`
   - **Database**: `aiagentsdb`
   - **Authentication kind**: Organisational account (Azure AD interactive) — recommended for initial setup
3. Click **Connect**, then select all tables except for tables with gold in name to mirror
4. Click **Mirror database**

**What happens next:**
Fabric performs an initial snapshot (5–15 min depending on table size), then continuously replicates changes. Monitor progress under the **Mirroring** tab → **Monitor**.

All mirrored status should show **Running** before proceeding.

### Grant Fabric read access to Azure SQL

Grab the Name from where you created the Workspace identity. 
Run in Query Editor:

```sql
-- Replace <fabric-spn-name> with the name shown in the Fabric mirror connection settings
CREATE USER [<fabric-spn-name>] FROM EXTERNAL PROVIDER;
ALTER ROLE db_datareader ADD MEMBER [<fabric-spn-name>];
```

After this succeeds go to your sql mirror and click refresh under Monitor Replication. You should see the 

---

## Phase 4 — Create the Lakehouses

### Create three lakehouses

In your workspace → **+ New item** → **Lakehouse** :

| Name | Purpose |
|------|---------|
| `AgentDemo_Bronze` | Mirrored raw Data |
| `AgentDemo_Silver` | Cleansed, standardised tables |
| `AgentDemo_Gold` | Pre-aggregated analytics tables queried by the app |


---

## Phase 4.1 — Bronze Layer — Seeding Notebook

1. Workspace → **+ New item** → **Notebook**
2. Name: `Bronze_Seed`
3. Click **Add lakehouse** → select `AgentDemo_Bronze` → **Add**

Notebook sources:

- `notebooks/01_bronze_seed_demo_data.py`

Paste the following cells and **Run all**:

---

## Phase 4.2 — Silver Layer — Cleansing Notebook

1. Workspace → **+ New item** → **Notebook**
2. Name: `Silver_Transform`
3. Click **Add lakehouse** → select `AgentDemo_Silver` → **Add**

Paste the following cells and **Run all**:

Notebook sources:

- `notebooks/02_silver_transform.py`

Run the Silver transformation flow and confirm the expected Silver tables are created
---

## Phase 4.3 — Gold Layer — Aggregation Notebook

1. Workspace → **+ New item** → **Notebook**
2. Name: `Gold_Aggregate`
3. Click **Add lakehouse** → select `AgentDemo_Gold` → **Add**
4. Add another Cell copy contents for Validate notebook file

Paste each cell and **Run all**:

Notebook sources:

- `notebooks/03_gold_aggregate.py`
- `notebooks/04_validate_gold.py`

Run the Gold aggregation notebook, then run the validation notebook.


---

## Phase 5 — Build the Refresh Pipeline

1. Workspace → **+ New item** → **Data pipeline**
2. Name: `Medallion_Refresh`

### Add activities

| # | Type | Name | Notebook |
|---|------|------|----------|
| 1 | Notebook | Run Silver | `Silver_Transform` |
| 2 | Notebook | Run Gold | `Gold_Aggregate` |

**Set dependency:** Click the green arrow on the `Run Silver` activity → drag it to `Run Gold`. This ensures Gold only runs after Silver completes successfully.

### Schedule the pipeline

1. Click **Schedule** in the pipeline toolbar → **+ New schedule**
2. Set: **Daily**, **Start time = 02:00 UTC**
3. Click **Apply**

### Test manually

Click **Run** → **Run now**. Monitor the run under the **Pipeline runs** tab in the workspace.

---

## Phase 6 - Semantic Model and Direct Lake

1. Build the semantic model over curated Gold data.
2. Prefer Direct Lake when the Gold data already lives in Fabric.
3. Avoid unnecessary DirectQuery fallback.
4. Validate behavior before cutover.

See **[FABRIC_DIRECT_LAKE.md](FABRIC_DIRECT_LAKE.md)**. for directions

---

## Phase 7 - Data Agent Deployment

1. Create the Fabric Data Agent in the target Fabric workspace.
2. Add the curated Gold source.
3. Select only approved tables.
4. Add clear agent instructions that explain what the source contains and what kinds of questions it should answer.
5. Add example queries where supported.
6. Test and refine the Data Agent in Fabric.
7. Publish the Data Agent only after validation.

See **[FABRIC_DATA_AGENT_DEPLOYMENT.md](FABRIC_DATA_AGENT_DEPLOYMENT.md)**. 


## Phase 8 — Connect the App to Fabric Gold

### Get the SQL Analytics Endpoint

1. Open the `AgentDemo_Gold` lakehouse in Fabric
2. Click the **SQL analytics endpoint** button in the top ribbon (or switch views in the top-right dropdown)
3. Copy the **Server** value — it looks like:
   `<workspace-name>-<guid>.datawarehouse.fabric.microsoft.com`

### Set App Service environment variables

```powershell
az webapp config appsettings set `
  --name <your-app-name> `
  --resource-group reg-admin `
  --settings `
    FABRIC_SQL_SERVER="<endpoint>.datawarehouse.fabric.microsoft.com" `
    FABRIC_SQL_DATABASE="AgentDemo_Gold" `
    FABRIC_WORKSPACE_ID="<workspace-guid>"
```

Or set them in **Azure Portal → App Service → Settings → Environment variables**.

---

### Restart the app

```powershell
az webapp restart --name <your-app-name> --resource-group reg-admin
```

Tail startup logs to confirm the Fabric connection initialises:

```powershell
az webapp log tail --name <your-app-name> --resource-group reg-admin
```

The AI agents and all analytics dashboards will now query Fabric Gold tables.

---

## Verification

### Check mirroring status

Fabric workspace → Mirrored database → **Monitor** tab
All tables should show **Running** with a recent sync timestamp.

### Check Gold tables exist

`AgentDemo_Gold` lakehouse → **Tables** pane
Expected tables: `gold_sales_time_series`, `gold_customer_360`, `gold_sales_performance`, `gold_geographic_sales`, `gold_cohort_analysis`, `gold_inventory_analysis`

### Verify app is hitting Fabric

In the app startup log, look for:
```
Fabric connection string set — agents will query Fabric
```

Or make a chat request asking about sales data and check that the agent returns data.

## Phase 9 optional deployments

### RTI Deployment
See **[FABRIC_RTI_DEPLOYMENT.md](FABRIC_RTI_DEPLOYMENT.md)**. 

### Purview Deployment
See **[PURVIEW_DEPLOYMENT.md](PURVIEW_DEPLOYMENT.md)**. 


### Run the smoke test

```bash
python tests/smoke_test.py --url https://<app-name>.azurewebsites.net --skip-auth
```

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Mirroring stuck at "Initializing" | Run the `ALTER DATABASE ... SET CHANGE_TRACKING = ON` command in SQL Query Editor. |
| Mirror shows "Pending" for individual tables | Ensure each table has a primary key — Fabric mirroring requires PKs. |
| Permission denied creating mirror | Grant the Fabric service principal `db_datareader` on Azure SQL (see Phase 3). |
| Gold tables empty after pipeline run | Run `Gold_Aggregate` notebook manually; check the **Spark logs** for errors. |
| App still querying Azure SQL after env var change | Restart the app: `az webapp restart`. Check `FABRIC_SQL_SERVER` is set and not empty. |
| SQL analytics endpoint unreachable | Fabric capacity may be paused. Resume it in **Fabric Admin → Capacity settings**. |
| `Login failed` for Fabric SQL endpoint | The App Service managed identity needs access. In Fabric workspace → Access, add the managed identity as **Contributor**. |
| PySpark errors in Silver notebook | Check the mirrored DB name in the `mirrored_db` variable matches the item name in your workspace exactly. |

---

## Reference: Gold Table Schema

The following tables are expected by the app's API routes and AI agent tools.
They are created by the `Gold_Aggregate` notebook above.

| Table | Used by |
|-------|---------|
| `gold_sales_time_series` | Analytics timeseries, sales metrics, goals |
| `gold_customer_360` | Deals endpoint, deal detail, agent tools |
| `gold_upsell_opportunities` | Deals endpoint, deal detail |
| `gold_sales_performance` | Sales metrics win rate, predictive insights |
| `gold_geographic_sales` | Agent geographic queries |
| `gold_cohort_analysis` | Analytics cohort dashboard |
| `gold_inventory_analysis` | Agent inventory queries |

> `gold_upsell_opportunities` is not generated by the notebooks above — it requires an ML scoring model or can be seeded manually. For demos, the `synthetic_data.sql` script includes 15 sample rows.