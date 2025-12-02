CREATE TABLE [dbo].[gold_outlier_summary_by_product_state] (

	[ProductID] int NULL, 
	[ProductName] varchar(8000) NULL, 
	[State] varchar(8000) NULL, 
	[outlier_count] bigint NULL, 
	[avg_outlier_price] decimal(27,6) NULL, 
	[avg_z_score] float NULL
);