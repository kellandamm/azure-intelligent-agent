CREATE TABLE [dbo].[gold_upsell_opportunities] (

	[CustomerID] int NULL, 
	[FirstName] varchar(8000) NULL, 
	[LastName] varchar(8000) NULL, 
	[Email] varchar(8000) NULL, 
	[State] varchar(8000) NULL, 
	[lifetime_value] decimal(22,2) NULL, 
	[order_count] bigint NULL, 
	[HealthScore] decimal(5,2) NULL, 
	[last_order_date] datetime2(6) NULL, 
	[upsell_score] float NULL, 
	[recommended_action] varchar(8000) NULL
);