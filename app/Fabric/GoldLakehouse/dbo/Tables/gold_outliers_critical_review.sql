CREATE TABLE [dbo].[gold_outliers_critical_review] (

	[OrderID] int NULL, 
	[OrderItemID] int NULL, 
	[OrderDate] datetime2(6) NULL, 
	[ProductName] varchar(8000) NULL, 
	[CategoryName] varchar(8000) NULL, 
	[AccountTypeID] int NULL, 
	[AccountTypeName] varchar(8000) NULL, 
	[EffectivePricePerUnit] decimal(23,2) NULL, 
	[avg_price_per_unit] decimal(27,6) NULL, 
	[price_z_score] float NULL, 
	[price_deviation_pct] decimal(38,6) NULL, 
	[outlier_type] varchar(8000) NULL, 
	[State] varchar(8000) NULL
);