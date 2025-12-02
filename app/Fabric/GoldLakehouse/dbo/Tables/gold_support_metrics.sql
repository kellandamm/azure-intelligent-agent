CREATE TABLE [dbo].[gold_support_metrics] (

	[CustomerID] int NULL, 
	[total_tickets] bigint NULL, 
	[open_tickets] bigint NULL, 
	[critical_tickets] bigint NULL, 
	[avg_resolution_time] float NULL, 
	[support_health] varchar(8000) NULL, 
	[FirstName] varchar(8000) NULL, 
	[LastName] varchar(8000) NULL, 
	[Email] varchar(8000) NULL
);