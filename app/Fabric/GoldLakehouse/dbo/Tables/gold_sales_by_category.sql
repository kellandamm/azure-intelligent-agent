CREATE TABLE [dbo].[gold_sales_by_category] (

	[CategoryID] int NULL, 
	[CategoryName] varchar(8000) NULL, 
	[total_revenue] decimal(22,2) NULL, 
	[transaction_count] bigint NULL, 
	[total_units_sold] bigint NULL, 
	[avg_transaction_value] decimal(16,6) NULL, 
	[unique_orders] bigint NULL
);