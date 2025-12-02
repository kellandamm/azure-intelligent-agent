CREATE TABLE [dbo].[gold_product_influence] (

	[ProductID] int NULL, 
	[ProductName] varchar(8000) NULL, 
	[CategoryName] varchar(8000) NULL, 
	[Price] decimal(10,2) NULL, 
	[order_frequency] bigint NULL, 
	[unique_customers] bigint NULL, 
	[total_revenue] decimal(22,2) NULL, 
	[influence_score] decimal(10,2) NULL
);