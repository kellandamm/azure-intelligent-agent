CREATE TABLE [dbo].[graph_demo_product_affinity] (

	[ProductID_a] bigint NULL, 
	[ProductID_b] bigint NULL, 
	[TimesPurchasedTogether] bigint NULL, 
	[ProductA_Name] varchar(8000) NULL, 
	[ProductB_Name] varchar(8000) NULL, 
	[AffinityScore] float NULL
);