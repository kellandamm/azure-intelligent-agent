"""
View table schemas in the Azure SQL Database
Database: <your-sql-server>.database.windows.net/<your-database>
"""

import os
import pyodbc
import struct
from azure.identity import DefaultAzureCredential

# Database connection configuration
SERVER = os.getenv('SQL_SERVER', '<your-sql-server>.database.windows.net')
DATABASE = os.getenv('SQL_DATABASE', 'aiagentsdb')

def get_azure_ad_token():
    """Get Azure AD access token for SQL Database"""
    credential = DefaultAzureCredential()
    token = credential.get_token("https://database.windows.net/.default")
    return token.token

def get_connection():
    """Create and return database connection"""
    token = get_azure_ad_token()
    token_bytes = token.encode('utf-16-le')
    token_struct = struct.pack(f'<I{len(token_bytes)}s', len(token_bytes), token_bytes)
    
    conn_string = (
        f'Driver={{ODBC Driver 18 for SQL Server}};'
        f'Server=tcp:{SERVER},1433;'
        f'Database={DATABASE};'
        f'Encrypt=yes;'
        f'TrustServerCertificate=no;'
        f'Connection Timeout=30;'
    )
    return pyodbc.connect(conn_string, attrs_before={1256: token_struct})

def view_table_schema(cursor, table_name):
    """View schema for a specific table"""
    print(f"\n{'='*100}")
    print(f"TABLE: {table_name}")
    print(f"{'='*100}")
    
    # Get columns
    cursor.execute(f"""
        SELECT 
            c.COLUMN_NAME,
            c.DATA_TYPE,
            c.CHARACTER_MAXIMUM_LENGTH,
            c.NUMERIC_PRECISION,
            c.NUMERIC_SCALE,
            c.IS_NULLABLE,
            c.COLUMN_DEFAULT
        FROM INFORMATION_SCHEMA.COLUMNS c
        WHERE c.TABLE_SCHEMA = 'dbo' 
        AND c.TABLE_NAME = '{table_name}'
        ORDER BY c.ORDINAL_POSITION
    """)
    
    columns = cursor.fetchall()
    
    print(f"{'Column Name':<30} {'Data Type':<25} {'Nullable':<10} {'Default':<30}")
    print("-" * 100)
    
    for col in columns:
        col_name = col.COLUMN_NAME
        
        # Build data type string
        data_type = col.DATA_TYPE.upper()
        if col.CHARACTER_MAXIMUM_LENGTH and col.CHARACTER_MAXIMUM_LENGTH > 0:
            if col.CHARACTER_MAXIMUM_LENGTH == -1:
                data_type += "(MAX)"
            else:
                data_type += f"({col.CHARACTER_MAXIMUM_LENGTH})"
        elif col.NUMERIC_PRECISION:
            if col.NUMERIC_SCALE:
                data_type += f"({col.NUMERIC_PRECISION},{col.NUMERIC_SCALE})"
            else:
                data_type += f"({col.NUMERIC_PRECISION})"
        
        nullable = "YES" if col.IS_NULLABLE == 'YES' else "NO"
        default = col.COLUMN_DEFAULT if col.COLUMN_DEFAULT else ""
        
        print(f"{col_name:<30} {data_type:<25} {nullable:<10} {default:<30}")
    
    # Get primary keys
    cursor.execute(f"""
        SELECT 
            kcu.COLUMN_NAME
        FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
        JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE kcu
            ON tc.CONSTRAINT_NAME = kcu.CONSTRAINT_NAME
        WHERE tc.TABLE_SCHEMA = 'dbo'
        AND tc.TABLE_NAME = '{table_name}'
        AND tc.CONSTRAINT_TYPE = 'PRIMARY KEY'
    """)
    
    pk_columns = [row.COLUMN_NAME for row in cursor.fetchall()]
    if pk_columns:
        print(f"\n🔑 Primary Key: {', '.join(pk_columns)}")
    
    # Get foreign keys
    cursor.execute(f"""
        SELECT 
            fk.name AS FK_Name,
            OBJECT_NAME(fk.parent_object_id) AS Table_Name,
            COL_NAME(fkc.parent_object_id, fkc.parent_column_id) AS Column_Name,
            OBJECT_NAME(fk.referenced_object_id) AS Referenced_Table,
            COL_NAME(fkc.referenced_object_id, fkc.referenced_column_id) AS Referenced_Column
        FROM sys.foreign_keys AS fk
        INNER JOIN sys.foreign_key_columns AS fkc 
            ON fk.object_id = fkc.constraint_object_id
        WHERE OBJECT_NAME(fk.parent_object_id) = '{table_name}'
    """)
    
    fk_rows = cursor.fetchall()
    if fk_rows:
        print(f"\n🔗 Foreign Keys:")
        for fk in fk_rows:
            print(f"   {fk.Column_Name} → {fk.Referenced_Table}.{fk.Referenced_Column}")
    
    # Get indexes
    cursor.execute(f"""
        SELECT 
            i.name AS Index_Name,
            i.type_desc AS Index_Type,
            COL_NAME(ic.object_id, ic.column_id) AS Column_Name
        FROM sys.indexes i
        INNER JOIN sys.index_columns ic 
            ON i.object_id = ic.object_id 
            AND i.index_id = ic.index_id
        WHERE OBJECT_NAME(i.object_id) = '{table_name}'
        AND i.type > 0
        ORDER BY i.name, ic.key_ordinal
    """)
    
    indexes = cursor.fetchall()
    if indexes:
        print(f"\n📇 Indexes:")
        current_index = None
        for idx in indexes:
            if idx.Index_Name != current_index:
                current_index = idx.Index_Name
                print(f"   {idx.Index_Name} ({idx.Index_Type}): ", end="")
            else:
                print(f", {idx.Column_Name}", end="")
            if indexes[-1].Index_Name == current_index and idx == [i for i in indexes if i.Index_Name == current_index][-1]:
                print()

def main():
    """Main execution function"""
    print("=" * 100)
    print(" " * 30 + "AZURE SQL DATABASE - TABLE SCHEMAS")
    print("=" * 100)
    print(f"Server:   {SERVER}")
    print(f"Database: {DATABASE}")
    print("=" * 100)
    
    try:
        # Connect to database
        print("\nConnecting to database...")
        conn = get_connection()
        cursor = conn.cursor()
        print("✓ Connected successfully\n")
        
        # List of tables
        tables = ['Categories', 'Products', 'Customers', 'Orders', 'OrderItems']
        
        # View schema for each table
        for table in tables:
            view_table_schema(cursor, table)
        
        # Summary
        print("\n" + "=" * 100)
        print("📊 SUMMARY")
        print("=" * 100)
        
        cursor.execute("""
            SELECT 
                t.TABLE_NAME,
                (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS c 
                 WHERE c.TABLE_NAME = t.TABLE_NAME AND c.TABLE_SCHEMA = 'dbo') AS Column_Count
            FROM INFORMATION_SCHEMA.TABLES t
            WHERE t.TABLE_SCHEMA = 'dbo' 
            AND t.TABLE_TYPE = 'BASE TABLE'
            ORDER BY t.TABLE_NAME
        """)
        
        print(f"\n{'Table Name':<30} {'Columns':<10}")
        print("-" * 40)
        for row in cursor.fetchall():
            print(f"{row.TABLE_NAME:<30} {row.Column_Count:<10}")
        
        print("\n" + "=" * 100)
        print("✓ Schema display completed successfully!")
        print("=" * 100)
        
        conn.close()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
