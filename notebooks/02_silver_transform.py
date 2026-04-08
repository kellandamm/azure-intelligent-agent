# Fabric notebook source: Silver transform
# Purpose: convert raw Bronze data to conformed Silver dimensions and facts

import json
from datetime import datetime
from pyspark.sql import functions as F

# ============================================
# PARAMETERS / CONFIG
# ============================================
BRONZE_SCHEMA = "AgentDemo_Bronze.dbo"
start_time = datetime.now()

try:
    run_date = mssparkutils.env.getJobIdParam("run_date")
except:
    run_date = start_time.isoformat()

execution_metrics = {
    "notebook": "Silver_transform",
    "start_time": start_time.isoformat(),
    "run_date": str(run_date),
    "status": "Running"
}

try:
    print("=" * 80)
    print("SILVER TRANSFORM STARTED")
    print("=" * 80)

    # ============================================
    # READ BRONZE TABLES FROM BRONZE LAKEHOUSE
    # ============================================
    bronze_geography = spark.read.table(f"{BRONZE_SCHEMA}.bronze_geography_raw")
    bronze_categories = spark.read.table(f"{BRONZE_SCHEMA}.bronze_categories_raw")
    bronze_products = spark.read.table(f"{BRONZE_SCHEMA}.bronze_products_raw")
    bronze_customers = spark.read.table(f"{BRONZE_SCHEMA}.bronze_customers_raw")
    bronze_orders = spark.read.table(f"{BRONZE_SCHEMA}.bronze_orders_raw")
    bronze_order_items = spark.read.table(f"{BRONZE_SCHEMA}.bronze_order_items_raw")
    bronze_opportunities = spark.read.table(f"{BRONZE_SCHEMA}.bronze_opportunities_raw")
    bronze_interactions = spark.read.table(f"{BRONZE_SCHEMA}.bronze_customer_interactions_raw")
    bronze_tickets = spark.read.table(f"{BRONZE_SCHEMA}.bronze_support_tickets_raw")
    bronze_metrics = spark.read.table(f"{BRONZE_SCHEMA}.bronze_customer_metrics_raw")
    bronze_inventory = spark.read.table(f"{BRONZE_SCHEMA}.bronze_inventory_snapshots_raw")

    execution_metrics["bronze_geography"] = bronze_geography.count()
    execution_metrics["bronze_categories"] = bronze_categories.count()
    execution_metrics["bronze_products"] = bronze_products.count()
    execution_metrics["bronze_customers"] = bronze_customers.count()
    execution_metrics["bronze_orders"] = bronze_orders.count()
    execution_metrics["bronze_order_items"] = bronze_order_items.count()
    execution_metrics["bronze_opportunities"] = bronze_opportunities.count()
    execution_metrics["bronze_interactions"] = bronze_interactions.count()
    execution_metrics["bronze_tickets"] = bronze_tickets.count()
    execution_metrics["bronze_metrics"] = bronze_metrics.count()
    execution_metrics["bronze_inventory"] = bronze_inventory.count()

    # ============================================
    # DATE DIMENSION
    # ============================================
    max_days = 730
    dim_date = (
        spark.range(0, max_days)
        .select(F.date_sub(F.current_date(), F.col("id").cast("int")).alias("date"))
        .select(
            "date",
            F.year("date").alias("year"),
            F.month("date").alias("month"),
            F.dayofmonth("date").alias("day"),
            F.dayofweek("date").alias("day_of_week"),
            F.date_format("date", "EEEE").alias("day_name"),
            F.date_format("date", "MMMM").alias("month_name"),
            F.ceil(F.month("date") / F.lit(3.0)).cast("int").alias("quarter"),
            F.concat(F.lit("Q"), F.ceil(F.month("date") / F.lit(3.0)).cast("int")).alias("quarter_name"),
            F.when(F.dayofweek("date").isin([1, 7]), F.lit(True)).otherwise(F.lit(False)).alias("is_weekend"),
            (F.year("date") * 100 + F.month("date")).alias("year_month_key"),
            F.current_timestamp().alias("processed_timestamp")
        )
    )

    dim_date.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable("dim_date")

    # ============================================
    # DIMENSIONS
    # ============================================
    dim_geography = (
        bronze_geography
        .withColumn(
            "population_tier",
            F.when(F.col("population") >= 15000000, "Large")
             .when(F.col("population") >= 8000000, "Medium")
             .otherwise("Small")
        )
        .withColumn("processed_timestamp", F.current_timestamp())
    )

    dim_category = (
        bronze_categories
        .dropDuplicates()
        .withColumn("category_id", F.monotonically_increasing_id() + F.lit(1))
        .withColumn("processed_timestamp", F.current_timestamp())
    )

    dim_product = (
        bronze_products
        .dropDuplicates(["product_id"])
        .withColumn(
            "profit_margin",
            F.when(
                F.col("base_price").isNotNull() & (F.col("base_price") != 0),
                (F.col("base_price") - F.col("cost")) / F.col("base_price")
            ).otherwise(None)
        )
        .withColumn(
            "price_tier",
            F.when(F.col("base_price") < 25, "Budget")
             .when(F.col("base_price") < 100, "Mid-Range")
             .when(F.col("base_price") < 500, "Premium")
             .otherwise("Luxury")
        )
        .withColumn("processed_timestamp", F.current_timestamp())
    )

    dim_customer = (
        bronze_customers
        .dropDuplicates(["customer_id"])
        .withColumn(
            "account_type_id",
            F.when(F.col("account_type") == "Enterprise", 1)
             .when(F.col("account_type") == "Business", 2)
             .when(F.col("account_type") == "Professional", 3)
             .otherwise(4)
        )
        .withColumn("customer_age_days", F.datediff(F.current_date(), F.col("customer_since")))
        .withColumn("processed_timestamp", F.current_timestamp())
    )

    dim_geography.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable("dim_geography")
    dim_category.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable("dim_category")
    dim_product.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable("dim_product")
    dim_customer.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable("dim_customer")

    # ============================================
    # FACTS
    # ============================================
    fact_orders = (
        bronze_orders
        .dropDuplicates(["order_id"])
        .withColumn("days_to_ship", F.datediff(F.col("shipped_date"), F.col("order_date")))
        .withColumn("days_to_deliver", F.datediff(F.col("delivered_date"), F.col("order_date")))
        .withColumn("processed_timestamp", F.current_timestamp())
    )

    product_prices = dim_product.select("product_id", F.col("base_price").alias("unit_price"))

    fact_order_items = (
        bronze_order_items
        .dropDuplicates(["order_item_id"])
        .join(product_prices, "product_id", "left")
        .withColumn(
            "line_total",
            F.round(F.col("quantity") * F.col("unit_price") * (1 - F.col("discount_pct") / 100), 2)
        )
        .withColumn("processed_timestamp", F.current_timestamp())
    )

    order_totals = fact_order_items.groupBy("order_id").agg(F.sum("line_total").alias("subtotal"))

    fact_orders = (
        fact_orders
        .join(order_totals, "order_id", "left")
        .fillna({"subtotal": 0})
        .withColumn("tax_amount", F.round(F.col("subtotal") * 0.08, 2))
        .withColumn("total_amount", F.col("subtotal") + F.col("tax_amount") + F.coalesce(F.col("shipping_cost"), F.lit(0)))
    )

    fact_opportunities = (
        bronze_opportunities
        .dropDuplicates(["opportunity_id"])
        .withColumn(
            "days_in_pipeline",
            F.when(
                F.col("actual_close_date").isNotNull(),
                F.datediff(F.col("actual_close_date"), F.col("created_date"))
            ).otherwise(F.datediff(F.current_date(), F.col("created_date")))
        )
        .withColumn("weighted_value", F.col("estimated_value") * F.col("probability_pct") / 100)
        .withColumn("processed_timestamp", F.current_timestamp())
    )

    fact_customer_interactions = bronze_interactions.dropDuplicates().withColumn("processed_timestamp", F.current_timestamp())
    fact_support_tickets = bronze_tickets.dropDuplicates(["ticket_id"]).withColumn("processed_timestamp", F.current_timestamp())
    fact_customer_metrics = bronze_metrics.dropDuplicates(["customer_id"]).withColumn("processed_timestamp", F.current_timestamp())
    fact_product_inventory = bronze_inventory.dropDuplicates().withColumn("processed_timestamp", F.current_timestamp())

    fact_orders.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable("fact_orders")
    fact_order_items.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable("fact_order_items")
    fact_opportunities.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable("fact_opportunities")
    fact_customer_interactions.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable("fact_customer_interactions")
    fact_support_tickets.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable("fact_support_tickets")
    fact_customer_metrics.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable("fact_customer_metrics")
    fact_product_inventory.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable("fact_product_inventory")

    # ============================================
    # LOGGING
    # ============================================
    end_time = datetime.now()
    execution_metrics["end_time"] = end_time.isoformat()
    execution_metrics["duration_seconds"] = (end_time - start_time).total_seconds()
    execution_metrics["status"] = "Success"

    log_row = {
        "notebook": execution_metrics["notebook"],
        "start_time": str(execution_metrics["start_time"]),
        "run_date": str(execution_metrics["run_date"]),
        "status": execution_metrics["status"],
        "bronze_geography": execution_metrics.get("bronze_geography"),
        "bronze_categories": execution_metrics.get("bronze_categories"),
        "bronze_products": execution_metrics.get("bronze_products"),
        "bronze_customers": execution_metrics.get("bronze_customers"),
        "bronze_orders": execution_metrics.get("bronze_orders"),
        "bronze_order_items": execution_metrics.get("bronze_order_items"),
        "bronze_opportunities": execution_metrics.get("bronze_opportunities"),
        "bronze_interactions": execution_metrics.get("bronze_interactions"),
        "bronze_tickets": execution_metrics.get("bronze_tickets"),
        "bronze_metrics": execution_metrics.get("bronze_metrics"),
        "bronze_inventory": execution_metrics.get("bronze_inventory"),
        "end_time": str(execution_metrics["end_time"]),
        "duration_seconds": float(execution_metrics["duration_seconds"]),
        "error_message": str(execution_metrics.get("error_message", ""))
    }

    spark.createDataFrame([log_row]) \
        .write.format("delta").mode("append").saveAsTable("pipeline_execution_log")

    print("Silver transform complete")
    mssparkutils.notebook.exit(json.dumps({"status": "success", "metrics": execution_metrics}, default=str))

except Exception as e:
    end_time = datetime.now()
    execution_metrics["end_time"] = end_time.isoformat()
    execution_metrics["duration_seconds"] = (end_time - start_time).total_seconds()
    execution_metrics["status"] = "Failed"
    execution_metrics["error_message"] = str(e)

result_payload = None

try:
    # all your processing here

    end_time = datetime.now()
    execution_metrics["end_time"] = end_time.isoformat()
    execution_metrics["duration_seconds"] = (end_time - start_time).total_seconds()
    execution_metrics["status"] = "Success"

    log_row = {
        "notebook": execution_metrics["notebook"],
        "start_time": str(execution_metrics["start_time"]),
        "run_date": str(execution_metrics["run_date"]),
        "status": execution_metrics["status"],
        "bronze_geography": execution_metrics.get("bronze_geography"),
        "bronze_categories": execution_metrics.get("bronze_categories"),
        "bronze_products": execution_metrics.get("bronze_products"),
        "bronze_customers": execution_metrics.get("bronze_customers"),
        "bronze_orders": execution_metrics.get("bronze_orders"),
        "bronze_order_items": execution_metrics.get("bronze_order_items"),
        "bronze_opportunities": execution_metrics.get("bronze_opportunities"),
        "bronze_interactions": execution_metrics.get("bronze_interactions"),
        "bronze_tickets": execution_metrics.get("bronze_tickets"),
        "bronze_metrics": execution_metrics.get("bronze_metrics"),
        "bronze_inventory": execution_metrics.get("bronze_inventory"),
        "end_time": str(execution_metrics["end_time"]),
        "duration_seconds": float(execution_metrics["duration_seconds"]),
        "error_message": str(execution_metrics.get("error_message", ""))
    }

    spark.createDataFrame([log_row]).write.format("delta").mode("append").saveAsTable("pipeline_execution_log")
    result_payload = {"status": "success", "metrics": execution_metrics}

except Exception as e:
    end_time = datetime.now()
    execution_metrics["end_time"] = end_time.isoformat()
    execution_metrics["duration_seconds"] = (end_time - start_time).total_seconds()
    execution_metrics["status"] = "Failed"
    execution_metrics["error_message"] = str(e)

    try:
        log_row = {
            "notebook": execution_metrics["notebook"],
            "start_time": str(execution_metrics["start_time"]),
            "run_date": str(execution_metrics["run_date"]),
            "status": execution_metrics["status"],
            "bronze_geography": execution_metrics.get("bronze_geography"),
            "bronze_categories": execution_metrics.get("bronze_categories"),
            "bronze_products": execution_metrics.get("bronze_products"),
            "bronze_customers": execution_metrics.get("bronze_customers"),
            "bronze_orders": execution_metrics.get("bronze_orders"),
            "bronze_order_items": execution_metrics.get("bronze_order_items"),
            "bronze_opportunities": execution_metrics.get("bronze_opportunities"),
            "bronze_interactions": execution_metrics.get("bronze_interactions"),
            "bronze_tickets": execution_metrics.get("bronze_tickets"),
            "bronze_metrics": execution_metrics.get("bronze_metrics"),
            "bronze_inventory": execution_metrics.get("bronze_inventory"),
            "end_time": str(execution_metrics["end_time"]),
            "duration_seconds": float(execution_metrics["duration_seconds"]),
            "error_message": str(execution_metrics.get("error_message", ""))
        }

        spark.createDataFrame([log_row]).write.format("delta").mode("append").saveAsTable("pipeline_execution_log")
    except:
        pass

    result_payload = {"status": "failed", "error": str(e), "metrics": execution_metrics}

mssparkutils.notebook.exit(json.dumps(result_payload, default=str))
