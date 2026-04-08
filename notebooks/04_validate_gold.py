# Fabric notebook source: Gold validation
# Purpose: validate Gold outputs before semantic model refresh

import json
from datetime import datetime
from pyspark.sql import functions as F

# ============================================
# PARAMETERS / CONFIG
# ============================================
GOLD_SCHEMA = "AgentDemo_Gold.dbo"
VALIDATION_RESULTS_TABLE = "gold_validation_results_v2"
start_time = datetime.now()
result_payload = None

try:
    run_date = mssparkutils.env.getJobIdParam("run_date")
except:
    run_date = start_time.isoformat()

execution_metrics = {
    "notebook": "Gold_validation",
    "start_time": start_time.isoformat(),
    "run_date": str(run_date),
    "status": "Running"
}

required_gold_tables = [
    "gold_customer_360",
    "gold_product_performance",
    "gold_sales_by_category",
    "gold_sales_time_series",
    "gold_geographic_sales",
    "gold_sales_pipeline",
    "gold_customer_rfm",
    "gold_support_metrics"
]

null_checks = [
    ("gold_customer_360", "customer_id"),
    ("gold_product_performance", "product_id"),
    ("gold_sales_time_series", "date"),
    ("gold_geographic_sales", "state_code")
]

try:
    print("=" * 80)
    print("GOLD VALIDATION STARTED")
    print("=" * 80)

    results = []
    total_failures = 0

    for table_name in required_gold_tables:
        full_table_name = f"{GOLD_SCHEMA}.{table_name}"

        try:
            df = spark.read.table(full_table_name)
            exists = True
            row_count = df.count()
        except Exception:
            exists = False
            row_count = 0

        exists_status = "PASS" if exists else "FAIL"
        rowcount_status = "PASS" if row_count > 0 else "FAIL"

        results.append((table_name, "table_exists", exists_status, str(exists), datetime.now().isoformat()))
        results.append((table_name, "row_count_gt_zero", rowcount_status, str(row_count), datetime.now().isoformat()))

        if exists_status == "FAIL":
            total_failures += 1
        if rowcount_status == "FAIL":
            total_failures += 1

        execution_metrics[f"{table_name}_exists"] = exists
        execution_metrics[f"{table_name}_rows"] = row_count

    for table_name, column_name in null_checks:
        full_table_name = f"{GOLD_SCHEMA}.{table_name}"

        try:
            null_count = spark.read.table(full_table_name).filter(F.col(column_name).isNull()).count()
            null_status = "PASS" if null_count == 0 else "FAIL"
        except Exception:
            null_count = -1
            null_status = "FAIL"

        results.append((table_name, f"null_check_{column_name}", null_status, str(null_count), datetime.now().isoformat()))

        if null_status == "FAIL":
            total_failures += 1

        execution_metrics[f"{table_name}_{column_name}_nulls"] = null_count

    validation_df = spark.createDataFrame(
        results,
        ["table_name", "check_name", "status", "detail", "checked_at"]
    )

    validation_df.write.format("delta")         .mode("overwrite")         .option("overwriteSchema", "true")         .saveAsTable(VALIDATION_RESULTS_TABLE)

    execution_metrics["validation_results_rows"] = validation_df.count()
    execution_metrics["failure_count"] = total_failures

    end_time = datetime.now()
    execution_metrics["end_time"] = end_time.isoformat()
    execution_metrics["duration_seconds"] = (end_time - start_time).total_seconds()

    if total_failures > 0:
        execution_metrics["status"] = "Failed"
        execution_metrics["error_message"] = f"Gold validation failed with {total_failures} failing checks"
        print(execution_metrics["error_message"])
        result_payload = {
            "status": "failed",
            "error": execution_metrics["error_message"],
            "metrics": execution_metrics
        }
    else:
        execution_metrics["status"] = "Success"
        print("Gold validation complete")
        result_payload = {
            "status": "success",
            "metrics": execution_metrics
        }

except Exception as e:
    end_time = datetime.now()
    execution_metrics["end_time"] = end_time.isoformat()
    execution_metrics["duration_seconds"] = (end_time - start_time).total_seconds()
    execution_metrics["status"] = "Failed"
    execution_metrics["error_message"] = str(e)

    print(f"Gold validation failed: {e}")
    result_payload = {
        "status": "failed",
        "error": str(e),
        "metrics": execution_metrics
    }

mssparkutils.notebook.exit(json.dumps(result_payload, default=str))