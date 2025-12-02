CREATE TABLE [dbo].[gold_shipping_performance] (

	[ShippingState] varchar(8000) NULL, 
	[shipment_count] bigint NULL, 
	[avg_days_to_ship] float NULL, 
	[min_days_to_ship] int NULL, 
	[max_days_to_ship] int NULL, 
	[median_days_to_ship] int NULL, 
	[p95_days_to_ship] int NULL, 
	[performance_rating] varchar(8000) NULL
);