CREATE TABLE [dbo].[silver_customers] (

	[CustomerID] int NULL, 
	[FirstName] varchar(8000) NULL, 
	[LastName] varchar(8000) NULL, 
	[Email] varchar(8000) NULL, 
	[PhoneNumber] varchar(8000) NULL, 
	[Address] varchar(8000) NULL, 
	[City] varchar(8000) NULL, 
	[State] varchar(8000) NULL, 
	[ZipCode] varchar(8000) NULL, 
	[Country] varchar(8000) NULL, 
	[CustomerSince] datetime2(6) NULL, 
	[IsActive] bit NULL, 
	[CreatedDate] datetime2(6) NULL, 
	[ModifiedDate] datetime2(6) NULL, 
	[_pii_masked] bit NULL, 
	[processed_timestamp] datetime2(6) NULL, 
	[_purview_classification] varchar(8000) NULL, 
	[_rls_filtered] bit NULL, 
	[_user_territories] varchar(8000) NULL, 
	[_processed_by_user] varchar(8000) NULL
);