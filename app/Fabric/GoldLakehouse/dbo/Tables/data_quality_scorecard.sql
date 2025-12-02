CREATE TABLE [dbo].[data_quality_scorecard] (

	[column_name] varchar(8000) NULL, 
	[total_records] bigint NULL, 
	[non_null_count] bigint NULL, 
	[null_count] bigint NULL, 
	[completeness_pct] float NULL, 
	[check_timestamp] varchar(8000) NULL
);