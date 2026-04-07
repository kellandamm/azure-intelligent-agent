# Notebook 01: Bronze seed demo data
# Purpose: land raw operational/demo data into Bronze Lakehouse tables.

from pyspark.sql import functions as F

source_tables = [
    'dimcustomer', 'dimproduct', 'factorders', 'factorderitems',
    'factopportunities', 'factsupporttickets', 'factcustomermetrics'
]

for table_name in source_tables:
    df = spark.read.table(table_name)
    bronze_name = f"bronze_{table_name}"
    df.withColumn('bronze_loaded_at', F.current_timestamp())       .write.format('delta').mode('overwrite').saveAsTable(bronze_name)
