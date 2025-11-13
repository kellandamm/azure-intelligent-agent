"""
Deploy database schema using Azure AD authentication
"""
import os
import pyodbc
import struct
from azure.identity import DefaultAzureCredential

def get_azure_ad_token():
    """Get Azure AD access token for SQL Database"""
    credential = DefaultAzureCredential()
    token = credential.get_token("https://database.windows.net/.default")
    return token.token

def deploy_schema():
    """Deploy the database schema"""
    SERVER = os.getenv('SQL_SERVER', 'aiagentsdemo.database.windows.net')
    DATABASE = os.getenv('SQL_DATABASE', 'aiagentsdb')
    
    print("=" * 70)
    print("Deploying Database Schema")
    print("=" * 70)
    print(f"Server:   {SERVER}")
    print(f"Database: {DATABASE}")
    print("=" * 70)
    
    try:
        # Get token and connect
        print("\nGetting Azure AD token...")
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
        
        print("Connecting to database...")
        conn = pyodbc.connect(conn_string, attrs_before={1256: token_struct})
        conn.autocommit = True  # Enable autocommit for DDL statements
        cursor = conn.cursor()
        print("✓ Connected\n")
        
        # Read and execute schema.sql
        print("Reading schema.sql...")
        with open('schema.sql', 'r') as f:
            schema_sql = f.read()
        
        # Split by GO statements and execute each batch
        batches = [batch.strip() for batch in schema_sql.split('GO') if batch.strip()]
        
        print(f"Executing {len(batches)} SQL batches...\n")
        
        for i, batch in enumerate(batches, 1):
            if batch.strip():
                try:
                    print(f"Batch {i}/{len(batches)}...", end=' ')
                    cursor.execute(batch)
                    print("✓")
                except Exception as e:
                    print(f"✗ Error: {e}")
                    # Continue with other batches
        
        print("\n" + "=" * 70)
        print("Schema Deployment Complete!")
        print("=" * 70)
        
        # Verify tables were created
        cursor.execute("""
            SELECT TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_SCHEMA = 'dbo'
            ORDER BY TABLE_NAME
        """)
        
        tables = [row[0] for row in cursor.fetchall()]
        print(f"\nTables created: {len(tables)}")
        for table in tables:
            print(f"  ✓ {table}")
        
        # Check category count
        cursor.execute("SELECT COUNT(*) FROM dbo.Categories")
        cat_count = cursor.fetchone()[0]
        print(f"\n✓ Categories seeded: {cat_count} records")
        
        conn.close()
        print("\n" + "=" * 70)
        return True
        
    except Exception as e:
        print(f"\n✗ Deployment failed: {e}")
        return False

if __name__ == "__main__":
    success = deploy_schema()
    exit(0 if success else 1)
