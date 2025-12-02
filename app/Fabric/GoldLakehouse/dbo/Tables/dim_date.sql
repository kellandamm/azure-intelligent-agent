CREATE TABLE [dbo].[dim_date] (

	[date] date NULL, 
	[year] int NULL, 
	[month] int NULL, 
	[day] int NULL, 
	[day_of_week] int NULL, 
	[day_name] varchar(8000) NULL, 
	[month_name] varchar(8000) NULL, 
	[quarter] int NULL, 
	[quarter_name] varchar(8000) NULL, 
	[is_weekend] bit NULL, 
	[season] varchar(8000) NULL, 
	[year_month_key] int NULL, 
	[year_month] varchar(8000) NULL
);