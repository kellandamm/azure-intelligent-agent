CREATE TABLE [dbo].[gold_hot_leads] (

	[OpportunityID] int NULL, 
	[OpportunityName] varchar(8000) NULL, 
	[CustomerID] int NULL, 
	[Stage] varchar(8000) NULL, 
	[EstimatedValue] decimal(12,2) NULL, 
	[ExpectedCloseDate] date NULL, 
	[AssignedTo] varchar(8000) NULL, 
	[lead_score] float NULL, 
	[priority] varchar(8000) NULL, 
	[interaction_count] bigint NULL, 
	[days_since_interaction] int NULL
);