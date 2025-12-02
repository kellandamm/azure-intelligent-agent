CREATE TABLE [dbo].[gold_customer_communities] (

	[State] varchar(8000) NULL, 
	[CustomerID] int NULL, 
	[FirstName] varchar(8000) NULL, 
	[LastName] varchar(8000) NULL, 
	[order_count] bigint NULL, 
	[total_spent] decimal(22,2) NULL, 
	[spending_tier] varchar(8000) NULL
);