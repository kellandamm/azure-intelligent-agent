"""
Test endpoint to discover Fabric Lakehouse schema
Access this via: /api/test/fabric-schema
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
import logging
from utils.db_connection import DatabaseConnection

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/test", tags=["testing"])

@router.get("/fabric-schema")
async def discover_fabric_schema():
    """
    Discover and return the Fabric Lakehouse schema.
    This endpoint helps identify available tables and columns.
    """
    try:
        with DatabaseConnection() as conn:
            cursor = conn.cursor()
            
            result = {
                "connection": "successful",
                "schemas": [],
                "tables": [],
                "gold_tables": []
            }
            
            # Get all schemas
            logger.info("Fetching schemas...")
            cursor.execute("""
                SELECT DISTINCT TABLE_SCHEMA 
                FROM INFORMATION_SCHEMA.TABLES 
                ORDER BY TABLE_SCHEMA
            """)
            result["schemas"] = [row[0] for row in cursor.fetchall()]
            
            # Get all tables
            logger.info("Fetching tables...")
            cursor.execute("""
                SELECT TABLE_SCHEMA, TABLE_NAME, TABLE_TYPE
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_TYPE = 'BASE TABLE'
                ORDER BY TABLE_SCHEMA, TABLE_NAME
            """)
            
            for schema, table, table_type in cursor.fetchall():
                table_info = {
                    "schema": schema,
                    "name": table,
                    "full_name": f"{schema}.{table}",
                    "type": table_type
                }
                
                # Get column info
                cursor.execute("""
                    SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
                    FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?
                    ORDER BY ORDINAL_POSITION
                """, schema, table)
                
                table_info["columns"] = [
                    {
                        "name": col_name,
                        "type": data_type,
                        "nullable": nullable == "YES"
                    }
                    for col_name, data_type, nullable in cursor.fetchall()
                ]
                
                # Get row count
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM [{schema}].[{table}]")
                    table_info["row_count"] = cursor.fetchone()[0]
                except:
                    table_info["row_count"] = None
                
                result["tables"].append(table_info)
                
                # If it's a gold table, add to gold_tables
                if 'gold' in schema.lower() or 'gold' in table.lower():
                    result["gold_tables"].append(table_info)
            
            logger.info(f"Found {len(result['tables'])} tables, {len(result['gold_tables'])} gold tables")
            return result
            
    except Exception as e:
        logger.error(f"Error discovering schema: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to discover schema: {str(e)}"
        )

@router.get("/fabric-test-query")
async def test_fabric_query(table: str = "dbo.YourTableName"):
    """
    Test a simple query against a Fabric table.
    Example: /api/test/fabric-test-query?table=dbo.Customers
    """
    try:
        with DatabaseConnection() as conn:
            cursor = conn.cursor()
            
            # Validate table name (basic SQL injection prevention)
            if not all(c.isalnum() or c in '._' for c in table):
                raise HTTPException(400, "Invalid table name")
            
            # Get top 5 rows
            cursor.execute(f"SELECT TOP 5 * FROM {table}")
            
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            
            return {
                "table": table,
                "columns": columns,
                "row_count": len(rows),
                "sample_data": [dict(zip(columns, row)) for row in rows]
            }
            
    except Exception as e:
        logger.error(f"Error testing query: {e}")
        raise HTTPException(500, f"Query failed: {str(e)}")
