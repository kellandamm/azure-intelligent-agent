CREATE TABLE [dbo].[graph_demo_tickets] (

	[TicketID] bigint NULL, 
	[CustomerID] bigint NULL, 
	[OrderID] float NULL, 
	[TicketType] varchar(8000) NULL, 
	[Status] varchar(8000) NULL, 
	[Priority] varchar(8000) NULL, 
	[CreatedDate] datetime2(6) NULL, 
	[ResolvedDate] datetime2(6) NULL
);