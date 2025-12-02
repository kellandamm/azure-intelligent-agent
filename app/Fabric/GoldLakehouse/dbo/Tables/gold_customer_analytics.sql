CREATE TABLE [dbo].[gold_customer_analytics] (

	[customer_id] int NULL, 
	[name] varchar(8000) NULL, 
	[state] varchar(8000) NULL, 
	[signup_date] date NULL, 
	[total_transactions] bigint NULL, 
	[lifetime_value] float NULL, 
	[avg_order_value] float NULL, 
	[last_purchase_date] date NULL, 
	[customer_segment] varchar(8000) NULL
);