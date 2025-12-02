CREATE TABLE [dbo].[gold_customer_ltv_predictions] (

	[customer_id] int NULL, 
	[name] varchar(8000) NULL, 
	[lifetime_value] float NULL, 
	[predicted_ltv] float NULL, 
	[ltv_potential] float NULL, 
	[customer_segment] varchar(8000) NULL
);