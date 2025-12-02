CREATE TABLE [dbo].[graph_demo_customers] (

	[CustomerID] bigint NULL, 
	[FirstName] varchar(8000) NULL, 
	[LastName] varchar(8000) NULL, 
	[Email] varchar(8000) NULL, 
	[City] varchar(8000) NULL, 
	[State] varchar(8000) NULL, 
	[Country] varchar(8000) NULL, 
	[CustomerSince] date NULL, 
	[CustomerTier] varchar(8000) NULL, 
	[IsActive] bit NULL
);