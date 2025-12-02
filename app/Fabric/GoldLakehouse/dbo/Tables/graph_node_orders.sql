CREATE TABLE [dbo].[graph_node_orders] (

	[OrderID] int NULL, 
	[OrderDate] date NULL, 
	[OrderStatus] varchar(8000) NULL, 
	[TotalAmount] decimal(12,2) NULL, 
	[ShippingCity] varchar(8000) NULL, 
	[ShippingState] varchar(8000) NULL, 
	[PaymentMethod] varchar(8000) NULL
);