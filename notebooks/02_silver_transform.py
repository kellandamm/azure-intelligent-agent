# Notebook 02: Silver transform
# Purpose: standardize, conform, and quality-check Bronze data into Silver tables.

from pyspark.sql import functions as F

orders = spark.read.table('bronze_factorders')
order_items = spark.read.table('bronze_factorderitems')
customers = spark.read.table('bronze_dimcustomer')
products = spark.read.table('bronze_dimproduct')

silver_orders = orders.filter(F.col('orderstatus') != 'Cancelled')
silver_order_items = order_items.filter(F.col('quantity') > 0)

silver_orders.write.format('delta').mode('overwrite').saveAsTable('silver_factorders')
silver_order_items.write.format('delta').mode('overwrite').saveAsTable('silver_factorderitems')
customers.write.format('delta').mode('overwrite').saveAsTable('silver_dimcustomer')
products.write.format('delta').mode('overwrite').saveAsTable('silver_dimproduct')
