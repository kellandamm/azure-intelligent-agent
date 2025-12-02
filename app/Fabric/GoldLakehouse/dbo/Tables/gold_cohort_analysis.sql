CREATE TABLE [dbo].[gold_cohort_analysis] (

	[cohort_month] varchar(8000) NULL, 
	[months_since_first_order] int NULL, 
	[active_customers] bigint NULL, 
	[cohort_revenue] decimal(22,2) NULL, 
	[cohort_orders] bigint NULL, 
	[cohort_size] bigint NULL, 
	[retention_rate] decimal(5,2) NULL
);