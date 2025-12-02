"""
Diagnostic endpoints for Fabric connectivity and schema exploration
"""
from fastapi import APIRouter
from typing import Dict, List, Any
from utils.db_connection import DatabaseConnection
from config import settings
from app.routes_analytics import get_fabric_db_connection
import os

diagnostic_router = APIRouter(prefix="/api/diagnostic", tags=["diagnostic"])

@diagnostic_router.get("/fabric-test")
async def test_fabric_connection():
    """Test Fabric SQL connection"""
    results = {
        "fabric_server": settings.fabric_sql_server,
        "fabric_database": settings.fabric_sql_database,
        "in_azure": bool(os.getenv('WEBSITE_INSTANCE_ID')),
        "connection_method": "Service Principal" if settings.fabric_client_id else ("Managed Identity" if os.getenv('WEBSITE_INSTANCE_ID') else "Access Token"),
        "using_client_id": settings.fabric_client_id[:10] + "..." if settings.fabric_client_id else None,
        "status": "unknown"
    }
    
    try:
        db_conn = get_fabric_db_connection()
        with db_conn.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT @@VERSION as version")
            version = cursor.fetchone()[0]
            results["status"] = "✅ Connected"
            results["sql_version"] = version[:100]
            
            # Try to list tables
            cursor.execute("""
                SELECT COUNT(*) as table_count
                FROM INFORMATION_SCHEMA.TABLES
            """)
            results["table_count"] = cursor.fetchone()[0]
            
    except Exception as e:
        results["status"] = f"❌ Failed: {str(e)}"
    
    return results


@diagnostic_router.get("/fabric-schema")
async def get_fabric_schema() -> Dict[str, Any]:
    """
    Get complete schema information for all tables in Fabric GoldLakehouse.
    Shows tables, columns, data types, and sample row counts.
    """
    results = {
        "database": settings.fabric_sql_database,
        "connection_method": "Service Principal" if settings.fabric_client_id else "Managed Identity",
        "tables": []
    }
    
    try:
        db_conn = get_fabric_db_connection()
        with db_conn.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get all tables
            cursor.execute("""
                SELECT 
                    TABLE_SCHEMA,
                    TABLE_NAME,
                    TABLE_TYPE
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_TYPE = 'BASE TABLE'
                ORDER BY TABLE_SCHEMA, TABLE_NAME
            """)
            
            tables = cursor.fetchall()
            
            for table in tables:
                schema_name = table[0]
                table_name = table[1]
                full_table_name = f"{schema_name}.{table_name}" if schema_name else table_name
                
                table_info = {
                    "schema": schema_name,
                    "name": table_name,
                    "full_name": full_table_name,
                    "columns": []
                }
                
                # Get columns for this table
                cursor.execute("""
                    SELECT 
                        COLUMN_NAME,
                        DATA_TYPE,
                        IS_NULLABLE,
                        CHARACTER_MAXIMUM_LENGTH,
                        NUMERIC_PRECISION,
                        NUMERIC_SCALE
                    FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?
                    ORDER BY ORDINAL_POSITION
                """, schema_name, table_name)
                
                columns = cursor.fetchall()
                for col in columns:
                    col_info = {
                        "name": col[0],
                        "data_type": col[1],
                        "nullable": col[2] == 'YES',
                    }
                    if col[3]:  # Character length
                        col_info["max_length"] = col[3]
                    if col[4]:  # Numeric precision
                        col_info["precision"] = col[4]
                    if col[5]:  # Numeric scale
                        col_info["scale"] = col[5]
                    
                    table_info["columns"].append(col_info)
                
                # Get row count
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM [{schema_name}].[{table_name}]")
                    table_info["row_count"] = cursor.fetchone()[0]
                except:
                    table_info["row_count"] = "N/A"
                
                # Get sample of first row to show data
                try:
                    cursor.execute(f"SELECT TOP 1 * FROM [{schema_name}].[{table_name}]")
                    sample_row = cursor.fetchone()
                    if sample_row:
                        table_info["sample_row"] = {
                            col_info["name"]: str(sample_row[i])[:100] if sample_row[i] is not None else None
                            for i, col_info in enumerate(table_info["columns"])
                        }
                except:
                    table_info["sample_row"] = None
                
                results["tables"].append(table_info)
            
            results["status"] = "✅ Success"
            results["table_count"] = len(results["tables"])
            
    except Exception as e:
        results["status"] = f"❌ Failed: {str(e)}"
        results["error"] = str(e)
    
    return results


@diagnostic_router.get("/fabric-gold-tables")
async def get_gold_tables_schema() -> Dict[str, Any]:
    """
    Get schema specifically for gold tables (gold_customer_360, gold_upsell_opportunities, gold_sales_performance).
    Provides detailed column information needed for analytics queries.
    """
    gold_tables = [
        "gold_customer_360",
        "gold_upsell_opportunities", 
        "gold_sales_performance"
    ]
    
    results = {
        "database": settings.fabric_sql_database,
        "connection_method": "Service Principal" if settings.fabric_client_id else "Managed Identity",
        "gold_tables": {}
    }
    
    try:
        db_conn = get_fabric_db_connection()
        with db_conn.get_connection() as conn:
            cursor = conn.cursor()
            
            for table_name in gold_tables:
                # Try to find the table (might be in dbo schema or no schema)
                cursor.execute("""
                    SELECT 
                        TABLE_SCHEMA,
                        TABLE_NAME
                    FROM INFORMATION_SCHEMA.TABLES
                    WHERE TABLE_NAME = ? AND TABLE_TYPE = 'BASE TABLE'
                """, table_name)
                
                table_result = cursor.fetchone()
                if not table_result:
                    results["gold_tables"][table_name] = {"status": "❌ Not Found"}
                    continue
                
                schema_name = table_result[0]
                full_name = f"{schema_name}.{table_name}" if schema_name else table_name
                
                # Get columns
                cursor.execute("""
                    SELECT 
                        COLUMN_NAME,
                        DATA_TYPE,
                        IS_NULLABLE
                    FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?
                    ORDER BY ORDINAL_POSITION
                """, schema_name, table_name)
                
                columns = cursor.fetchall()
                column_list = [
                    {
                        "name": col[0],
                        "type": col[1],
                        "nullable": col[2] == 'YES'
                    }
                    for col in columns
                ]
                
                # Get row count
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM [{schema_name}].[{table_name}]")
                    row_count = cursor.fetchone()[0]
                except:
                    row_count = "N/A"
                
                # Get column names as simple list
                column_names = [col[0] for col in columns]
                
                results["gold_tables"][table_name] = {
                    "status": "✅ Found",
                    "schema": schema_name,
                    "full_name": full_name,
                    "row_count": row_count,
                    "column_count": len(columns),
                    "column_names": column_names,
                    "columns": column_list
                }
            
            results["status"] = "✅ Success"
            
    except Exception as e:
        results["status"] = f"❌ Failed: {str(e)}"
        results["error"] = str(e)
    
    return results
