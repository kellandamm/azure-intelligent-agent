CREATE TABLE [dbo].[gold_realtime_metrics] (

	[window_start] datetime2(6) NULL, 
	[window_end] datetime2(6) NULL, 
	[events_per_minute] bigint NULL, 
	[items_sold] bigint NULL
);