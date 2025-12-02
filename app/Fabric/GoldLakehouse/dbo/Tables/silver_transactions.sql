CREATE TABLE [dbo].[silver_transactions] (

	[transaction_id] bigint NULL, 
	[customer_id] bigint NULL, 
	[product_id] bigint NULL, 
	[quantity] int NULL, 
	[transaction_date] date NULL, 
	[payment_method] varchar(8000) NULL, 
	[total_amount] decimal(30,2) NULL, 
	[price] decimal(18,2) NULL, 
	[cost] decimal(18,2) NULL, 
	[total_cost] decimal(30,2) NULL, 
	[profit_margin] decimal(26,2) NULL, 
	[load_timestamp] datetime2(6) NULL, 
	[data_quality_score] int NULL, 
	[source_system] varchar(8000) NULL, 
	[processing_layer] varchar(8000) NULL
);