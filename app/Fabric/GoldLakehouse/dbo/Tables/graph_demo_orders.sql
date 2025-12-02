CREATE TABLE [dbo].[graph_demo_orders] (

	[OrderID] bigint NULL, 
	[CustomerID] bigint NULL, 
	[OrderDate] datetime2(6) NULL, 
	[OrderStatus] varchar(8000) NULL, 
	[TotalAmount] float NULL, 
	[PaymentMethod] varchar(8000) NULL, 
	[ShippingCity] varchar(8000) NULL, 
	[ShippingState] varchar(8000) NULL
);