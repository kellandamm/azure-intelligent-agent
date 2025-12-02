CREATE TABLE [dbo].[gold_quality_metrics] (

	[customer_records] bigint NULL, 
	[dimension_tables] bigint NULL, 
	[fact_tables] bigint NULL, 
	[measurement_date] datetime2(6) NULL, 
	[medallion_layer] varchar(8000) NULL, 
	[product_records] bigint NULL, 
	[quality_score] float NULL, 
	[record_count] bigint NULL, 
	[sales_records] bigint NULL
);