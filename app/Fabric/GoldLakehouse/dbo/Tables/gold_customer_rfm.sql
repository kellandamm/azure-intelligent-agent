CREATE TABLE [dbo].[gold_customer_rfm] (

	[CustomerID] int NULL, 
	[recency_days] int NULL, 
	[frequency] bigint NULL, 
	[monetary_value] decimal(22,2) NULL, 
	[R_score] int NULL, 
	[F_score] int NULL, 
	[M_score] int NULL, 
	[RFM_score] int NULL, 
	[customer_tier] varchar(8000) NULL, 
	[FirstName] varchar(8000) NULL, 
	[LastName] varchar(8000) NULL, 
	[Email] varchar(8000) NULL, 
	[State] varchar(8000) NULL
);