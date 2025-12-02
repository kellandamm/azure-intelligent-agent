CREATE TABLE [dbo].[gold_at_risk_customers] (

	[CustomerID] int NULL, 
	[FirstName] varchar(8000) NULL, 
	[LastName] varchar(8000) NULL, 
	[Email] varchar(8000) NULL, 
	[State] varchar(8000) NULL, 
	[HealthScore] decimal(5,2) NULL, 
	[RenewalRisk] varchar(8000) NULL, 
	[ContractEndDate] date NULL, 
	[last_purchase_date] datetime2(6) NULL, 
	[days_since_purchase] int NULL, 
	[open_tickets] bigint NULL, 
	[lifetime_value] decimal(22,2) NULL, 
	[churn_probability] int NULL, 
	[action_required] varchar(8000) NULL
);