CREATE TABLE [dbo].[medallion_lineage_metadata] (

	[source_layer] varchar(8000) NULL, 
	[source_table] varchar(8000) NULL, 
	[target_table] varchar(8000) NULL, 
	[transformation_type] varchar(8000) NULL, 
	[refresh_frequency] varchar(8000) NULL
);