# Fabric deployment

## Scope

This doc describes the optional Microsoft Fabric analytics path for the solution. Fabric should remain optional, while SQL remains the default live analytics path when Fabric is not enabled.

## Recommended Fabric items

- Bronze Lakehouse.
- Silver Lakehouse.
- Gold Lakehouse or Warehouse.
- Semantic model over curated Gold tables.
- Deployment pipeline for Dev/Test/Prod promotion.
- Optional Real-Time Intelligence and Data Agent capabilities.

## Notebook sources

Use repo notebook sources instead of large inline notebook bodies:

- `notebooks/01_bronze_seed_demo_data.py`
- `notebooks/02_silver_transform.py`
- `notebooks/03_gold_aggregate.py`
- `notebooks/04_validate_gold.py`

## Data flow

`Source systems or Azure SQL -> Bronze -> Silver -> Gold -> semantic model -> reports / app analytics / Data Agent`

## Direct Lake guidance

Direct Lake should be the preferred semantic model mode when Gold data is already curated in Fabric and the workload is lake-centric. Direct Lake is optimized for large volumes of Delta-backed data in OneLake, usually outperforms DirectQuery, and uses low-cost metadata framing instead of full import-style refresh copies. Designs should avoid DirectQuery fallback where possible because fallback can reduce query performance.

## Semantic model notes

- Prefer Direct Lake over curated Gold Delta tables.
- Avoid SQL views or SQL endpoint patterns that force DirectQuery fallback unless deliberately required.
- Validate permissions, semantic model ownership, and refresh behavior before production rollout.
- Prototype the semantic model design first to confirm Direct Lake is the right fit.

## Deployment pipeline guidance

Use Fabric deployment pipelines for promoted content across development, test, and production workspaces. Microsoft Fabric deployment pipelines support notebooks, Eventstream, Eventhouse, Real-time Dashboard, Data pipelines, Lakehouse items, and additional supported content types.

## Validation checklist

- Bronze loads successfully.
- Silver quality filters and conforming steps run successfully.
- Gold tables are queryable and stable.
- Semantic model points to curated Gold tables.
- Direct Lake behavior is validated for performance and fallback risk.
- Deployment pipeline pairing and promotion are tested.
