CREATE TABLE [dbo].[customer_summary] (

	[state] varchar(8000) NULL, 
	[customer_segment] varchar(8000) NULL, 
	[total_customers] bigint NULL, 
	[earliest_signup] date NULL, 
	[latest_signup] date NULL
);