CREATE TABLE [dbo].[gold_inventory_analysis] (

	[ProductID] int NULL, 
	[ProductName] varchar(8000) NULL, 
	[CategoryName] varchar(8000) NULL, 
	[SKU] varchar(8000) NULL, 
	[StockQuantity] int NULL, 
	[total_sold] bigint NULL, 
	[order_frequency] bigint NULL, 
	[stock_to_sales_ratio] float NULL, 
	[stock_status] varchar(8000) NULL, 
	[reorder_priority] int NULL
);