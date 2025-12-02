CREATE TABLE [dbo].[dim_product] (

	[base_price] float NULL, 
	[brand] varchar(8000) NULL, 
	[category_name] varchar(8000) NULL, 
	[cost] float NULL, 
	[is_active] bit NULL, 
	[lead_time_days] bigint NULL, 
	[product_id] bigint NULL, 
	[product_name] varchar(8000) NULL, 
	[rating] float NULL, 
	[reorder_level] bigint NULL, 
	[review_count] bigint NULL, 
	[sku] varchar(8000) NULL, 
	[stock_quantity] bigint NULL, 
	[supplier] varchar(8000) NULL, 
	[upc] varchar(8000) NULL, 
	[weight_oz] float NULL, 
	[profit_margin] float NULL, 
	[price_tier] varchar(8000) NULL
);