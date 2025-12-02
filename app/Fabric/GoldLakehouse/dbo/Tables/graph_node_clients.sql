CREATE TABLE [dbo].[graph_node_clients] (

	[ClientID] int NULL, 
	[Email] varchar(8000) NULL, 
	[FirstName] varchar(8000) NULL, 
	[LastName] varchar(8000) NULL, 
	[City] varchar(8000) NULL, 
	[State] varchar(8000) NULL, 
	[Country] varchar(8000) NULL, 
	[CustomerSince] datetime2(6) NULL, 
	[IsActive] bit NULL
);