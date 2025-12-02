CREATE TABLE [dbo].[gold_customer_features_ml] (

	[CustomerID] int NULL, 
	[State] varchar(8000) NULL, 
	[CustomerSince] datetime2(6) NULL, 
	[Country] varchar(8000) NULL, 
	[total_orders] bigint NULL, 
	[lifetime_value] decimal(22,2) NULL, 
	[avg_order_value] decimal(16,6) NULL, 
	[first_order_date] date NULL, 
	[last_order_date] date NULL, 
	[payment_methods_used] bigint NULL, 
	[avg_delivery_days] float NULL, 
	[customer_age_days] int NULL, 
	[days_since_last_order] int NULL, 
	[order_frequency] decimal(10,4) NULL, 
	[is_active] int NULL, 
	[churn_risk_score] int NULL
);