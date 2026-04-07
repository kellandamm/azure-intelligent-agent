# Notebook 03: Gold aggregate
# Purpose: publish curated Gold analytics tables for semantic models and Data Agent use.

from pyspark.sql import functions as F

orders = spark.read.table('silver_factorders')
items = spark.read.table('silver_factorderitems')
customers = spark.read.table('silver_dimcustomer')
products = spark.read.table('silver_dimproduct')

customer360 = orders.join(customers, 'customerid')     .groupBy('customerid', 'firstname', 'lastname', 'accounttype')     .agg(
        F.countDistinct('orderid').alias('totalorders'),
        F.sum('totalamount').alias('lifetimevalue'),
        F.max('orderdate').alias('lastorderdate')
    )

productperf = items.join(products, 'productid')     .groupBy('productid', 'productname', 'categoryname', 'brand')     .agg(
        F.sum('quantity').alias('totalunitssold'),
        F.sum('linetotal').alias('totalrevenue')
    )

customer360.write.format('delta').mode('overwrite').saveAsTable('gold_customer360')
productperf.write.format('delta').mode('overwrite').saveAsTable('gold_productperformance')
