CREATE TABLE [dbo].[gold_category_trends] (

	[CategoryID] int NULL, 
	[CategoryName] varchar(8000) NULL, 
	[year_month] varchar(8000) NULL, 
	[monthly_revenue] decimal(22,2) NULL, 
	[monthly_units_sold] bigint NULL, 
	[monthly_orders] bigint NULL, 
	[prev_month_revenue] decimal(22,2) NULL, 
	[revenue_growth_pct] decimal(5,2) NULL, 
	[trend_direction] varchar(8000) NULL
);