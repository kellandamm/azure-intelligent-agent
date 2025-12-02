CREATE TABLE [dbo].[gold_payment_analysis] (

	[PaymentMethod] varchar(8000) NULL, 
	[transaction_count] bigint NULL, 
	[total_revenue] decimal(22,2) NULL, 
	[avg_transaction_value] decimal(16,6) NULL, 
	[min_transaction] decimal(12,2) NULL, 
	[max_transaction] decimal(12,2) NULL, 
	[stddev_transaction] float NULL, 
	[revenue_share_pct] decimal(5,2) NULL
);