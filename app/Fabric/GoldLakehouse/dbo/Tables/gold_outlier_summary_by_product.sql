CREATE TABLE [dbo].[gold_outlier_summary_by_product] (

	[ProductID] int NULL, 
	[ProductName] varchar(8000) NULL, 
	[CategoryName] varchar(8000) NULL, 
	[outlier_count] bigint NULL, 
	[avg_outlier_price] decimal(27,6) NULL, 
	[min_outlier_price] decimal(23,2) NULL, 
	[max_outlier_price] decimal(23,2) NULL, 
	[avg_z_score] float NULL
);