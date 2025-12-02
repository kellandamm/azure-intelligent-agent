CREATE TABLE [dbo].[silver_products] (

	[ProductID] int NULL, 
	[ProductName] varchar(8000) NULL, 
	[CategoryID] int NULL, 
	[Price] decimal(10,2) NULL, 
	[StockQuantity] int NULL, 
	[Description] varchar(8000) NULL, 
	[SKU] varchar(8000) NULL, 
	[IsActive] bit NULL, 
	[CreatedDate] datetime2(6) NULL, 
	[ModifiedDate] datetime2(6) NULL, 
	[processed_timestamp] datetime2(6) NULL, 
	[_purview_classification] varchar(8000) NULL, 
	[_rls_filtered] bit NULL, 
	[_processed_by_user] varchar(8000) NULL
);