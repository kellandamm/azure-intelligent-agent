CREATE TABLE [dbo].[dim_category] (

	[category_name] varchar(8000) NULL, 
	[description] varchar(8000) NULL, 
	[department] varchar(8000) NULL, 
	[is_active] bit NULL, 
	[margin_pct] float NULL, 
	[category_id] bigint NULL
);