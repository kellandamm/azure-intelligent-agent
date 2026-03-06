"""
Fabric Lakehouse Schema Diagnostic Script

This script connects to Microsoft Fabric lakehouse to inspect the actual schema
and sample data available in the GoldLakehouse.

Usage:
    python diagnostic_fabric_schema.py

Requirements:
    - Fabric connection configured in .env
    - User has access to the lakehouse
"""

import sys
import os
from typing import List, Dict, Any, Optional
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings
from utils.db_connection import DatabaseConnection


class FabricSchemaDiagnostic:
    """Diagnose Fabric lakehouse schema and data availability."""
    
    def __init__(self):
        self.connection = DatabaseConnection(
            settings.fabric_connection_string,
            use_access_token=True,
            client_id=settings.fabric_client_id,
            client_secret=settings.fabric_client_secret,
            tenant_id=settings.effective_fabric_tenant_id,
        )
    
    def get_all_tables(self) -> List[Dict[str, str]]:
        """Get list of all tables in the lakehouse."""
        print("🔍 Querying for all tables in the lakehouse...")
        
        with self.connection.get_connection() as conn:
            cursor = conn.cursor()
            
            query = """
                SELECT 
                    TABLE_SCHEMA,
                    TABLE_NAME,
                    TABLE_TYPE
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_TYPE = 'BASE TABLE'
                ORDER BY TABLE_SCHEMA, TABLE_NAME
            """
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            tables = []
            for row in rows:
                tables.append({
                    "schema": row[0],
                    "name": row[1],
                    "type": row[2]
                })
            
            return tables
    
    def get_table_columns(self, schema: str, table_name: str) -> List[Dict[str, Any]]:
        """Get column definitions for a specific table."""
        with self.connection.get_connection() as conn:
            cursor = conn.cursor()
            
            query = """
                SELECT 
                    COLUMN_NAME,
                    DATA_TYPE,
                    CHARACTER_MAXIMUM_LENGTH,
                    NUMERIC_PRECISION,
                    NUMERIC_SCALE,
                    IS_NULLABLE,
                    COLUMN_DEFAULT
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?
                ORDER BY ORDINAL_POSITION
            """
            
            cursor.execute(query, (schema, table_name))
            rows = cursor.fetchall()
            
            columns = []
            for row in rows:
                columns.append({
                    "name": row[0],
                    "data_type": row[1],
                    "max_length": row[2],
                    "precision": row[3],
                    "scale": row[4],
                    "nullable": row[5],
                    "default": row[6]
                })
            
            return columns
    
    def get_table_row_count(self, schema: str, table_name: str) -> int:
        """Get row count for a table."""
        try:
            with self.connection.get_connection() as conn:
                cursor = conn.cursor()
                
                # Use QUOTENAME to safely escape schema and table name
                query = f"SELECT COUNT(*) FROM [{schema}].[{table_name}]"
                cursor.execute(query)
                
                return cursor.fetchone()[0]
        except Exception as e:
            print(f"  ⚠️ Error getting row count: {e}")
            return 0
    
    def get_sample_data(self, schema: str, table_name: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get sample rows from a table."""
        try:
            with self.connection.get_connection() as conn:
                cursor = conn.cursor()
                
                query = f"SELECT TOP {limit} * FROM [{schema}].[{table_name}]"
                cursor.execute(query)
                
                columns = [column[0] for column in cursor.description]
                rows = cursor.fetchall()
                
                samples = []
                for row in rows:
                    samples.append(dict(zip(columns, row)))
                
                return samples
        except Exception as e:
            print(f"  ⚠️ Error getting sample data: {e}")
            return []
    
    def check_date_ranges(self, schema: str, table_name: str) -> Optional[Dict[str, Any]]:
        """Check date ranges in tables with date columns."""
        try:
            columns = self.get_table_columns(schema, table_name)
            date_columns = [col["name"] for col in columns if "date" in col["data_type"].lower()]
            
            if not date_columns:
                return None
            
            with self.connection.get_connection() as conn:
                cursor = conn.cursor()
                
                date_ranges = {}
                for col in date_columns:
                    query = f"""
                        SELECT 
                            MIN([{col}]) as min_date,
                            MAX([{col}]) as max_date,
                            COUNT(DISTINCT [{col}]) as unique_dates
                        FROM [{schema}].[{table_name}]
                        WHERE [{col}] IS NOT NULL
                    """
                    cursor.execute(query)
                    row = cursor.fetchone()
                    
                    if row and row[0]:
                        date_ranges[col] = {
                            "min": row[0],
                            "max": row[1],
                            "unique_count": row[2]
                        }
                
                return date_ranges
        except Exception as e:
            print(f"  ⚠️ Error checking date ranges: {e}")
            return None
    
    def run_diagnostic(self):
        """Run complete diagnostic on Fabric lakehouse."""
        print("\n" + "="*80)
        print("📊 Fabric Lakehouse Schema Diagnostic")
        print("="*80 + "\n")
        
        print(f"🔗 Lakehouse: {settings.fabric_lakehouse_name}")
        print(f"🆔 Lakehouse ID: {settings.fabric_lakehouse_id}")
        print(f"🌐 Connection: {settings.fabric_connection_string[:50]}...\n")
        
        # Get all tables
        tables = self.get_all_tables()
        
        if not tables:
            print("❌ No tables found in the lakehouse!")
            print("\nℹ️ This might mean:")
            print("  1. The lakehouse is empty (no tables created yet)")
            print("  2. Connection string is incorrect")
            print("  3. User doesn't have permissions")
            return
        
        print(f"✅ Found {len(tables)} tables\n")
        
        # Analyze each table
        for table in tables:
            schema = table["schema"]
            name = table["name"]
            full_name = f"{schema}.{name}"
            
            print(f"{'='*80}")
            print(f"📋 Table: {full_name}")
            print(f"{'='*80}")
            
            # Get row count
            row_count = self.get_table_row_count(schema, name)
            print(f"  📊 Row Count: {row_count:,}")
            
            # Get columns
            columns = self.get_table_columns(schema, name)
            print(f"  📝 Columns: {len(columns)}")
            
            for col in columns:
                type_info = col["data_type"]
                if col["max_length"]:
                    type_info += f"({col['max_length']})"
                elif col["precision"]:
                    type_info += f"({col['precision']},{col['scale']})"
                
                nullable = "NULL" if col["nullable"] == "YES" else "NOT NULL"
                print(f"    - {col['name']:<30} {type_info:<20} {nullable}")
            
            # Check date ranges
            date_ranges = self.check_date_ranges(schema, name)
            if date_ranges:
                print(f"\n  📅 Date Ranges:")
                for col_name, ranges in date_ranges.items():
                    print(f"    - {col_name}:")
                    print(f"        Min: {ranges['min']}")
                    print(f"        Max: {ranges['max']}")
                    print(f"        Unique Dates: {ranges['unique_count']:,}")
            
            # Get sample data
            if row_count > 0:
                print(f"\n  🔍 Sample Data (first 3 rows):")
                samples = self.get_sample_data(schema, name, limit=3)
                
                for i, sample in enumerate(samples, 1):
                    print(f"\n    Row {i}:")
                    for key, value in sample.items():
                        # Truncate long values
                        str_value = str(value)
                        if len(str_value) > 50:
                            str_value = str_value[:47] + "..."
                        print(f"      {key}: {str_value}")
            
            print()
    
    def check_expected_tables(self):
        """Check if expected tables exist for Data Agents."""
        print("\n" + "="*80)
        print("✅ Expected Tables Check")
        print("="*80 + "\n")
        
        expected_tables = [
            "SalesFact",
            "CustomerDim",
            "ProductDim",
            "InventoryFact",
            "PerformanceMetrics"
        ]
        
        existing_tables = self.get_all_tables()
        existing_names = [t["name"] for t in existing_tables]
        
        for expected in expected_tables:
            if expected in existing_names:
                print(f"  ✅ {expected:<25} EXISTS")
                
                # Get quick stats
                for table in existing_tables:
                    if table["name"] == expected:
                        row_count = self.get_table_row_count(table["schema"], expected)
                        print(f"     └─ Row count: {row_count:,}")
                        
                        # Check for 2026 data if it's a fact table
                        if "Fact" in expected:
                            try:
                                with self.connection.get_connection() as conn:
                                    cursor = conn.cursor()
                                    
                                    # Try to find date column
                                    cols = self.get_table_columns(table["schema"], expected)
                                    date_col = next((c["name"] for c in cols if "date" in c["name"].lower()), None)
                                    
                                    if date_col:
                                        query = f"""
                                            SELECT COUNT(*) 
                                            FROM [{table["schema"]}].[{expected}]
                                            WHERE YEAR([{date_col}]) = 2026
                                        """
                                        cursor.execute(query)
                                        count_2026 = cursor.fetchone()[0]
                                        print(f"     └─ 2026 data: {count_2026:,} rows")
                            except Exception as e:
                                print(f"     └─ Could not check 2026 data: {e}")
            else:
                print(f"  ❌ {expected:<25} MISSING")


def main():
    """Run diagnostic."""
    try:
        diagnostic = FabricSchemaDiagnostic()
        diagnostic.run_diagnostic()
        diagnostic.check_expected_tables()
        
        print("\n" + "="*80)
        print("✅ Diagnostic Complete")
        print("="*80 + "\n")
        
        print("📝 Summary:")
        print("  - Review the tables and columns above")
        print("  - Verify that expected tables (SalesFact, CustomerDim, etc.) exist")
        print("  - Check that 2026 data is present for current analysis")
        print("  - Note any missing columns that agents are expecting")
        print("\n💡 Next Steps:")
        print("  1. Update agent prompts with actual column names")
        print("  2. Adjust queries to match the schema")
        print("  3. Populate missing tables or data as needed")
        print("  4. Test Data Agent queries with natural language\n")
        
    except Exception as e:
        print(f"\n❌ Error running diagnostic: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
