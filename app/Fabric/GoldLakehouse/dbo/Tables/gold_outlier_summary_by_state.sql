CREATE TABLE [dbo].[gold_outlier_summary_by_state] (

	[State] varchar(8000) NULL, 
	[outlier_count] bigint NULL, 
	[avg_outlier_price] decimal(27,6) NULL, 
	[high_price_count] bigint NULL, 
	[low_price_count] bigint NULL
);