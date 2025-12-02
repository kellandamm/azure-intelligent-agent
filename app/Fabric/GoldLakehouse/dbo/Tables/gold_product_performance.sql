CREATE TABLE [dbo].[gold_product_performance] (

	[ProductID] int NULL, 
	[ProductName] varchar(8000) NULL, 
	[CategoryID] int NULL, 
	[CategoryName] varchar(8000) NULL, 
	[Price] decimal(10,2) NULL, 
	[SKU] varchar(8000) NULL, 
	[total_units_sold] bigint NULL, 
	[times_ordered] bigint NULL, 
	[total_revenue] decimal(22,2) NULL, 
	[avg_discount_pct] decimal(9,6) NULL, 
	[revenue_rank] int NULL
);