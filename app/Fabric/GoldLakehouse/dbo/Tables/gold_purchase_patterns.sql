CREATE TABLE [dbo].[gold_purchase_patterns] (

	[CustomerID] int NULL, 
	[avg_days_between_orders] float NULL, 
	[min_days_between_orders] int NULL, 
	[max_days_between_orders] int NULL, 
	[stddev_days_between_orders] float NULL, 
	[repeat_orders] bigint NULL, 
	[purchase_frequency_segment] varchar(8000) NULL, 
	[FirstName] varchar(8000) NULL, 
	[LastName] varchar(8000) NULL, 
	[State] varchar(8000) NULL
);