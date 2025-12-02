CREATE TABLE [dbo].[graph_demo_products] (

	[ProductID] bigint NULL, 
	[ProductName] varchar(8000) NULL, 
	[CategoryID] bigint NULL, 
	[Price] float NULL, 
	[StockQuantity] bigint NULL, 
	[SKU] varchar(8000) NULL, 
	[Rating] float NULL, 
	[ReviewCount] bigint NULL, 
	[IsActive] bit NULL
);