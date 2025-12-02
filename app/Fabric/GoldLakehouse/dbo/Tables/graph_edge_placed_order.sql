CREATE TABLE [dbo].[graph_edge_placed_order] (

	[source_client_id] int NULL, 
	[target_order_id] int NULL, 
	[OrderDate] date NULL, 
	[TotalAmount] decimal(12,2) NULL
);