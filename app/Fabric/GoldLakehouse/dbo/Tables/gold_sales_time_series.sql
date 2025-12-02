CREATE TABLE [dbo].[gold_sales_time_series] (

	[OrderDate] date NULL, 
	[year] int NULL, 
	[quarter] int NULL, 
	[month] int NULL, 
	[month_name] varchar(8000) NULL, 
	[day_of_week] int NULL, 
	[daily_orders] bigint NULL, 
	[daily_revenue] decimal(22,2) NULL, 
	[avg_order_value] decimal(16,6) NULL, 
	[unique_customers] bigint NULL
);