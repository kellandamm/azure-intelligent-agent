# Fabric notebook source: Gold aggregate
# Purpose: build analytics-ready Gold tables from Silver dimensions and facts.

from pyspark.sql import functions as F
from pyspark.sql.window import Window

fact_orders = spark.read.table('fact_orders')
fact_order_items = spark.read.table('fact_order_items')
fact_opportunities = spark.read.table('fact_opportunities')
fact_support_tickets = spark.read.table('fact_support_tickets')
dim_customer = spark.read.table('dim_customer')
dim_product = spark.read.table('dim_product')
dim_geography = spark.read.table('dim_geography')
dim_date = spark.read.table('dim_date')

customer_360 = fact_orders.filter(F.col('order_status') != 'Cancelled').join(dim_customer, 'customer_id').groupBy('customer_id', 'first_name', 'last_name', 'email', 'state_code', 'account_type', 'customer_since').agg(F.count('order_id').alias('total_orders'), F.sum('total_amount').alias('lifetime_value'), F.avg('total_amount').alias('avg_order_value'), F.max('order_date').alias('last_order_date'), F.min('order_date').alias('first_order_date'), F.avg('days_to_ship').alias('avg_delivery_days')).withColumn('customer_tenure_days', F.datediff(F.current_date(), F.col('customer_since'))).withColumn('recency_days', F.datediff(F.current_date(), F.col('last_order_date'))).withColumn('customer_segment', F.when(F.col('lifetime_value') >= 10000, 'VIP').when(F.col('lifetime_value') >= 5000, 'High Value').when(F.col('lifetime_value') >= 1000, 'Medium Value').otherwise('Standard'))
customer_360.write.format('delta').mode('overwrite').saveAsTable('gold_customer_360')

product_performance = fact_order_items.join(dim_product, 'product_id').join(fact_orders.select('order_id', 'order_date', 'order_status'), 'order_id').filter(F.col('order_status') != 'Cancelled').groupBy('product_id', 'product_name', 'category_name', 'brand', 'base_price', 'sku').agg(F.sum('quantity').alias('total_units_sold'), F.count('order_item_id').alias('times_ordered'), F.sum('line_total').alias('total_revenue'), F.avg('discount_pct').alias('avg_discount_pct')).withColumn('revenue_rank', F.dense_rank().over(Window.orderBy(F.col('total_revenue').desc())))
product_performance.write.format('delta').mode('overwrite').saveAsTable('gold_product_performance')

sales_by_category = fact_order_items.join(dim_product.select('product_id', 'category_name'), 'product_id').join(fact_orders.select('order_id', 'order_status'), 'order_id').filter(F.col('order_status') != 'Cancelled').groupBy('category_name').agg(F.sum('line_total').alias('total_revenue'), F.count('order_item_id').alias('transaction_count'), F.sum('quantity').alias('total_units_sold'), F.avg('line_total').alias('avg_transaction_value'))
sales_by_category.write.format('delta').mode('overwrite').saveAsTable('gold_sales_by_category')

sales_time_series = fact_orders.filter(F.col('order_status') != 'Cancelled').join(dim_date, fact_orders.order_date.cast('date') == dim_date.date).groupBy('date', 'year', 'quarter', 'month', 'month_name', 'day_of_week').agg(F.count('order_id').alias('daily_orders'), F.sum('total_amount').alias('daily_revenue'), F.avg('total_amount').alias('avg_order_value'), F.countDistinct('customer_id').alias('unique_customers'))
sales_time_series.write.format('delta').mode('overwrite').saveAsTable('gold_sales_time_series')

geographic_sales = fact_orders.join(dim_customer.select('customer_id', 'state_code'), 'customer_id').join(dim_geography, 'state_code').filter(F.col('order_status') != 'Cancelled').groupBy('state_code', 'state_name', 'region', 'division').agg(F.count('order_id').alias('total_orders'), F.sum('total_amount').alias('total_revenue'), F.countDistinct('customer_id').alias('unique_customers'), F.avg('total_amount').alias('avg_order_value'))
geographic_sales.write.format('delta').mode('overwrite').saveAsTable('gold_geographic_sales')

sales_pipeline = fact_opportunities.filter(F.col('stage').isin(['Lead', 'Qualification', 'Proposal', 'Negotiation'])).groupBy('stage', 'assigned_to').agg(F.count('opportunity_id').alias('opportunity_count'), F.sum('estimated_value').alias('pipeline_value'), F.avg('probability_pct').alias('avg_probability'), F.sum('weighted_value').alias('weighted_pipeline_value'))
sales_pipeline.write.format('delta').mode('overwrite').saveAsTable('gold_sales_pipeline')

orders_for_rfm = fact_orders.filter(F.col('order_status') != 'Cancelled')
reference_date = orders_for_rfm.agg(F.max('order_date')).collect()[0][0]
rfm_data = orders_for_rfm.groupBy('customer_id').agg(F.datediff(F.lit(reference_date), F.max('order_date')).alias('recency_days'), F.count('order_id').alias('frequency'), F.sum('total_amount').alias('monetary_value'))
customer_rfm = rfm_data.withColumn('R_score', F.ntile(4).over(Window.orderBy('recency_days'))).withColumn('F_score', F.ntile(4).over(Window.orderBy(F.col('frequency').desc()))).withColumn('M_score', F.ntile(4).over(Window.orderBy(F.col('monetary_value').desc()))).withColumn('RFM_score', F.col('R_score') + F.col('F_score') + F.col('M_score')).withColumn('customer_tier', F.when(F.col('RFM_score') >= 10, 'Champions').when(F.col('RFM_score') >= 8, 'Loyal Customers').when(F.col('RFM_score') >= 6, 'Potential Loyalists').when(F.col('RFM_score') >= 5, 'At Risk').otherwise('Lost Customers')).join(dim_customer.select('customer_id', 'first_name', 'last_name', 'email', 'state_code'), 'customer_id')
customer_rfm.write.format('delta').mode('overwrite').saveAsTable('gold_customer_rfm')

support_metrics = fact_support_tickets.groupBy('customer_id', 'priority', 'status').agg(F.count('*').alias('ticket_count'), F.avg('resolution_time_hours').alias('avg_resolution_hours'), F.avg('satisfaction_score').alias('avg_satisfaction')).groupBy('customer_id').agg(F.sum('ticket_count').alias('total_tickets'), F.sum(F.when(F.col('status') == 'Open', F.col('ticket_count')).otherwise(0)).alias('open_tickets'), F.sum(F.when(F.col('priority') == 'Critical', F.col('ticket_count')).otherwise(0)).alias('critical_tickets'), F.avg('avg_resolution_hours').alias('avg_resolution_time'), F.avg('avg_satisfaction').alias('overall_satisfaction')).withColumn('support_health', F.when(F.col('open_tickets') == 0, 'Excellent').when(F.col('open_tickets') <= 2, 'Good').when(F.col('critical_tickets') > 0, 'Critical').otherwise('Needs Attention')).join(dim_customer.select('customer_id', 'first_name', 'last_name', 'email'), 'customer_id')
support_metrics.write.format('delta').mode('overwrite').saveAsTable('gold_support_metrics')

catalog_rows = [
    ('dim_date', 'Dimension', 'Date dimension for time intelligence'),
    ('dim_geography', 'Dimension', 'US states and regions'),
    ('dim_category', 'Dimension', 'Product categories and departments'),
    ('dim_product', 'Dimension', 'Product master data'),
    ('dim_customer', 'Dimension', 'Customer master data'),
    ('fact_orders', 'Fact', 'Order headers and transactions'),
    ('fact_order_items', 'Fact', 'Order line items'),
    ('fact_opportunities', 'Fact', 'Sales pipeline opportunities'),
    ('fact_customer_interactions', 'Fact', 'Customer touchpoints'),
    ('fact_support_tickets', 'Fact', 'Support tickets'),
    ('fact_customer_metrics', 'Fact', 'Customer health metrics'),
    ('fact_product_inventory', 'Fact', 'Inventory snapshots'),
    ('gold_customer_360', 'Gold', 'Customer 360 view'),
    ('gold_product_performance', 'Gold', 'Product sales performance'),
    ('gold_sales_by_category', 'Gold', 'Sales by category'),
    ('gold_sales_time_series', 'Gold', 'Daily sales trends'),
    ('gold_geographic_sales', 'Gold', 'Sales by geography'),
    ('gold_sales_pipeline', 'Gold', 'Sales pipeline summary'),
    ('gold_customer_rfm', 'Gold', 'RFM customer segmentation'),
    ('gold_support_metrics', 'Gold', 'Support metrics by customer')
]
records = []
for table_name, table_type, description in catalog_rows:
    df = spark.read.table(table_name)
    records.append((table_name, table_type, description, df.count(), len(df.columns)))
metadata_catalog = spark.createDataFrame(records, ['table_name', 'table_type', 'description', 'record_count', 'column_count'])
metadata_catalog.write.format('delta').mode('overwrite').saveAsTable('metadata_catalog')

print('Gold aggregate complete')