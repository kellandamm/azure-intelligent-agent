CREATE TABLE [dbo].[gold_order_funnel] (

	[OrderStatus] varchar(8000) NULL, 
	[order_count] bigint NULL, 
	[total_value] decimal(22,2) NULL, 
	[avg_order_value] decimal(16,6) NULL, 
	[unique_customers] bigint NULL, 
	[funnel_stage] int NULL, 
	[conversion_rate] decimal(5,2) NULL
);