# Fabric notebook source: Silver transform
# Purpose: convert raw Bronze data to conformed Silver dimensions and facts.

from pyspark.sql import functions as F

bronze_geography = spark.read.table('bronze_geography_raw')
bronze_categories = spark.read.table('bronze_categories_raw')
bronze_products = spark.read.table('bronze_products_raw')
bronze_customers = spark.read.table('bronze_customers_raw')
bronze_orders = spark.read.table('bronze_orders_raw')
bronze_order_items = spark.read.table('bronze_order_items_raw')
bronze_opportunities = spark.read.table('bronze_opportunities_raw')
bronze_interactions = spark.read.table('bronze_customer_interactions_raw')
bronze_tickets = spark.read.table('bronze_support_tickets_raw')
bronze_metrics = spark.read.table('bronze_customer_metrics_raw')
bronze_inventory = spark.read.table('bronze_inventory_snapshots_raw')

# Date dimension
max_days = 730
dim_date = spark.range(0, max_days).select(F.date_sub(F.current_date(), F.col('id').cast('int')).alias('date')).select(
    'date',
    F.year('date').alias('year'),
    F.month('date').alias('month'),
    F.dayofmonth('date').alias('day'),
    F.dayofweek('date').alias('day_of_week'),
    F.date_format('date', 'EEEE').alias('day_name'),
    F.date_format('date', 'MMMM').alias('month_name'),
    F.ceil(F.month('date') / F.lit(3.0)).cast('int').alias('quarter'),
    F.concat(F.lit('Q'), F.ceil(F.month('date') / F.lit(3.0)).cast('int')).alias('quarter_name'),
    F.when(F.dayofweek('date').isin([1, 7]), True).otherwise(False).alias('is_weekend'),
    (F.year('date') * 100 + F.month('date')).alias('year_month_key')
)
dim_date.write.format('delta').mode('overwrite').saveAsTable('dim_date')

# Dimensions
bronze_geography.withColumn('population_tier', F.when(F.col('population') >= 15000000, 'Large').when(F.col('population') >= 8000000, 'Medium').otherwise('Small')).write.format('delta').mode('overwrite').saveAsTable('dim_geography')
bronze_categories.withColumn('category_id', F.monotonically_increasing_id() + F.lit(1)).write.format('delta').mode('overwrite').saveAsTable('dim_category')
bronze_products.withColumn('profit_margin', (F.col('base_price') - F.col('cost')) / F.col('base_price')).withColumn('price_tier', F.when(F.col('base_price') < 25, 'Budget').when(F.col('base_price') < 100, 'Mid-Range').when(F.col('base_price') < 500, 'Premium').otherwise('Luxury')).write.format('delta').mode('overwrite').saveAsTable('dim_product')
bronze_customers.withColumn('account_type_id', F.when(F.col('account_type') == 'Enterprise', 1).when(F.col('account_type') == 'Business', 2).when(F.col('account_type') == 'Professional', 3).otherwise(4)).withColumn('customer_age_days', F.datediff(F.current_date(), F.col('customer_since'))).write.format('delta').mode('overwrite').saveAsTable('dim_customer')

# Facts
fact_orders = bronze_orders.withColumn('days_to_ship', F.datediff(F.col('shipped_date'), F.col('order_date'))).withColumn('days_to_deliver', F.datediff(F.col('delivered_date'), F.col('order_date')))
product_prices = spark.read.table('dim_product').select('product_id', F.col('base_price').alias('unit_price'))
fact_order_items = bronze_order_items.join(product_prices, 'product_id').withColumn('line_total', F.round(F.col('quantity') * F.col('unit_price') * (1 - F.col('discount_pct') / 100), 2))
order_totals = fact_order_items.groupBy('order_id').agg(F.sum('line_total').alias('subtotal'))
fact_orders = fact_orders.join(order_totals, 'order_id', 'left').fillna({'subtotal': 0}).withColumn('tax_amount', F.round(F.col('subtotal') * 0.08, 2)).withColumn('total_amount', F.col('subtotal') + F.col('tax_amount') + F.col('shipping_cost'))

fact_orders.write.format('delta').mode('overwrite').saveAsTable('fact_orders')
fact_order_items.write.format('delta').mode('overwrite').saveAsTable('fact_order_items')
bronze_opportunities.withColumn('days_in_pipeline', F.when(F.col('actual_close_date').isNotNull(), F.datediff(F.col('actual_close_date'), F.col('created_date'))).otherwise(F.datediff(F.current_date(), F.col('created_date')))).withColumn('weighted_value', F.col('estimated_value') * F.col('probability_pct') / 100).write.format('delta').mode('overwrite').saveAsTable('fact_opportunities')
bronze_interactions.write.format('delta').mode('overwrite').saveAsTable('fact_customer_interactions')
bronze_tickets.write.format('delta').mode('overwrite').saveAsTable('fact_support_tickets')
bronze_metrics.write.format('delta').mode('overwrite').saveAsTable('fact_customer_metrics')
bronze_inventory.write.format('delta').mode('overwrite').saveAsTable('fact_product_inventory')

print('Silver transform complete')
