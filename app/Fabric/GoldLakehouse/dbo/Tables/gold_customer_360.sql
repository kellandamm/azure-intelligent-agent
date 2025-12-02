CREATE TABLE [dbo].[gold_customer_360] (

	[CustomerID] int NULL, 
	[FirstName] varchar(8000) NULL, 
	[LastName] varchar(8000) NULL, 
	[Email] varchar(8000) NULL, 
	[City] varchar(8000) NULL, 
	[State] varchar(8000) NULL, 
	[Country] varchar(8000) NULL, 
	[CustomerSince] datetime2(6) NULL, 
	[total_orders] bigint NULL, 
	[lifetime_value] decimal(22,2) NULL, 
	[avg_order_value] decimal(16,6) NULL, 
	[last_order_date] date NULL, 
	[first_order_date] date NULL, 
	[avg_delivery_days] float NULL, 
	[customer_tenure_days] int NULL, 
	[recency_days] int NULL, 
	[customer_segment] varchar(8000) NULL, 
	[customer_status] varchar(8000) NULL
);