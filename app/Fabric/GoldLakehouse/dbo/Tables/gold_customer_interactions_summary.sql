CREATE TABLE [dbo].[gold_customer_interactions_summary] (

	[CustomerID] int NULL, 
	[total_interactions] bigint NULL, 
	[email_count] bigint NULL, 
	[call_count] bigint NULL, 
	[meeting_count] bigint NULL, 
	[positive_interactions] bigint NULL, 
	[negative_interactions] bigint NULL, 
	[last_interaction_date] datetime2(6) NULL, 
	[avg_interaction_duration] float NULL, 
	[sentiment_ratio] float NULL, 
	[FirstName] varchar(8000) NULL, 
	[LastName] varchar(8000) NULL, 
	[Email] varchar(8000) NULL
);