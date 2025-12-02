CREATE TABLE [dbo].[gold_product_betweenness] (

	[ProductID] int NULL, 
	[ProductName] varchar(8000) NULL, 
	[CategoryName] varchar(8000) NULL, 
	[unique_customers] bigint NULL, 
	[unique_orders] bigint NULL, 
	[betweenness_score] decimal(10,2) NULL
);