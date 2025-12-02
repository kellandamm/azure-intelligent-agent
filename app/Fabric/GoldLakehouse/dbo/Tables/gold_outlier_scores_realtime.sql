CREATE TABLE [dbo].[gold_outlier_scores_realtime] (

	[OrderID] int NULL, 
	[OrderItemID] int NULL, 
	[ProductName] varchar(8000) NULL, 
	[CategoryName] varchar(8000) NULL, 
	[State] varchar(8000) NULL, 
	[EffectivePricePerUnit] decimal(21,8) NULL, 
	[avg_price_per_unit] decimal(27,6) NULL, 
	[price_z_score] float NULL, 
	[prediction] float NULL, 
	[outlier_probability] float NULL, 
	[risk_level] varchar(8000) NULL, 
	[scored_timestamp] datetime2(6) NULL
);