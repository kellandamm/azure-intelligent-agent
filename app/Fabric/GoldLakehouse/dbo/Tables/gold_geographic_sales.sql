CREATE TABLE [dbo].[gold_geographic_sales] (

	[State] varchar(8000) NULL, 
	[City] varchar(8000) NULL, 
	[total_orders] bigint NULL, 
	[total_revenue] decimal(22,2) NULL, 
	[unique_customers] bigint NULL, 
	[avg_order_value] decimal(16,6) NULL, 
	[state_rank] int NULL
);