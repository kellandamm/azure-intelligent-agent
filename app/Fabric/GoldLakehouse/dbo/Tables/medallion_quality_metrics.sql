CREATE TABLE [dbo].[medallion_quality_metrics] (

	[duplicates] bigint NULL, 
	[measurement_date] datetime2(6) NULL, 
	[medallion_layer] varchar(8000) NULL, 
	[quality_score] float NULL, 
	[record_count] bigint NULL
);