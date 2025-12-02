CREATE TABLE [dbo].[staging_eventhouse_events] (

	[customer_id] bigint NULL, 
	[product_id] bigint NULL, 
	[event_id] varchar(8000) NULL, 
	[payment_method] varchar(8000) NULL, 
	[quantity] bigint NULL, 
	[timestamp] datetime2(6) NULL, 
	[ingestion_time] datetime2(6) NULL, 
	[event_hour] int NULL, 
	[event_minute] int NULL, 
	[product_name] varchar(8000) NULL, 
	[category] varchar(8000) NULL, 
	[price] float NULL, 
	[name] varchar(8000) NULL, 
	[state] varchar(8000) NULL
);