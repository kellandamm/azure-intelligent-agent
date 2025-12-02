CREATE TABLE [dbo].[graph_demo_reviews] (

	[ReviewID] bigint NULL, 
	[CustomerID] bigint NULL, 
	[ProductID] bigint NULL, 
	[Rating] bigint NULL, 
	[ReviewText] varchar(8000) NULL, 
	[ReviewDate] datetime2(6) NULL, 
	[IsVerifiedPurchase] bit NULL
);