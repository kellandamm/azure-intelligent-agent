CREATE TABLE [dbo].[gold_product_affinity] (

	[product_b_id] int NULL, 
	[product_a_id] int NULL, 
	[times_purchased_together] bigint NULL, 
	[product_a_name] varchar(8000) NULL, 
	[product_a_category] varchar(8000) NULL, 
	[product_b_name] varchar(8000) NULL, 
	[product_b_category] varchar(8000) NULL, 
	[affinity_score] decimal(5,2) NULL
);