# Fabric notebook source: Gold validation
# Purpose: validate Gold outputs before semantic model refresh.

from pyspark.sql import functions as F
from datetime import datetime

required_gold_tables = [
    'gold_customer_360',
    'gold_product_performance',
    'gold_sales_by_category',
    'gold_sales_time_series',
    'gold_geographic_sales',
    'gold_sales_pipeline',
    'gold_customer_rfm',
    'gold_support_metrics'
]

results = []
for table_name in required_gold_tables:
    exists = spark.catalog.tableExists(table_name)
    row_count = spark.read.table(table_name).count() if exists else 0
    results.append((table_name, 'table_exists', 'PASS' if exists else 'FAIL', str(exists), datetime.now()))
    results.append((table_name, 'row_count_gt_zero', 'PASS' if row_count > 0 else 'FAIL', str(row_count), datetime.now()))

null_checks = [
    ('gold_customer_360', 'customer_id'),
    ('gold_product_performance', 'product_id'),
    ('gold_sales_time_series', 'date'),
    ('gold_geographic_sales', 'state_code')
]
for table_name, column_name in null_checks:
    null_count = spark.read.table(table_name).filter(F.col(column_name).isNull()).count()
    results.append((table_name, f'null_check_{column_name}', 'PASS' if null_count == 0 else 'FAIL', str(null_count), datetime.now()))

spark.createDataFrame(results, ['table_name', 'check_name', 'status', 'detail', 'checked_at']).write.format('delta').mode('overwrite').saveAsTable('gold_validation_results')

failures = spark.read.table('gold_validation_results').filter(F.col('status') == 'FAIL').count()
if failures > 0:
    raise Exception(f'Gold validation failed with {failures} failing checks')

print('Gold validation complete')