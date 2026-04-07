# Notebook 04: Validate Gold
# Purpose: basic Gold-layer validation before semantic model/report refresh.

validation = []
for table_name in ['gold_customer360', 'gold_productperformance']:
    count_value = spark.read.table(table_name).count()
    validation.append((table_name, count_value, count_value > 0))

validation_df = spark.createDataFrame(validation, ['table_name', 'row_count', 'passed'])
validation_df.write.format('delta').mode('overwrite').saveAsTable('gold_validation_results')
