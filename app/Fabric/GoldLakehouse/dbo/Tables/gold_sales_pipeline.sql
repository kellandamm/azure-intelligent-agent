CREATE TABLE [dbo].[gold_sales_pipeline] (

	[Stage] varchar(8000) NULL, 
	[AssignedTo] varchar(8000) NULL, 
	[opportunity_count] bigint NULL, 
	[pipeline_value] decimal(22,2) NULL, 
	[avg_probability] decimal(9,6) NULL, 
	[weighted_pipeline_value] decimal(32,8) NULL
);