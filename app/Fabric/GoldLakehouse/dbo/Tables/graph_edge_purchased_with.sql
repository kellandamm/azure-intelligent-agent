CREATE TABLE [dbo].[graph_edge_purchased_with] (

	[source_item_id] int NULL, 
	[target_item_id] int NULL, 
	[times_purchased_together] bigint NULL, 
	[affinity_score] decimal(5,2) NULL
);