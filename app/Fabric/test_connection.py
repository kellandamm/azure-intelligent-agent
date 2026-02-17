"""
Test database connection using Azure AD authentication
"""
import os
import pyodbc
import struct
from azure.identity import DefaultAzureCredential, InteractiveBrowserCredential

def get_azure_ad_token():
    """Get Azure AD access token for SQL Database"""
    try:
        # Try DefaultAzureCredential first (uses current Azure CLI login)
        credential = DefaultAzureCredential()
        token = credential.get_token("https://database.windows.net/.default")
        return token.token
    except Exception as e:
        print(f"DefaultAzureCredential failed: {e}")
        print("Trying InteractiveBrowserCredential...")
        # Fall back to interactive browser login
        credential = InteractiveBrowserCredential()
        token = credential.get_token("https://database.windows.net/.default")
        return token.token

def test_connection():
    """Test connection to Azure SQL Database"""
    SERVER = os.getenv('SQL_SERVER', '<your-sql-server>.database.windows.net')
    DATABASE = os.getenv('SQL_DATABASE', 'aiagentsdb')
    
    print("=" * 60)
    print("Testing Azure SQL Database Connection")
    print("=" * 60)
    print(f"Server:   {SERVER}")
    print(f"Database: {DATABASE}")
    print(f"Auth:     Azure AD (Interactive)")
    print("=" * 60)
    
    try:
        print("\nGetting Azure AD token...")
        token = get_azure_ad_token()
        print("✓ Azure AD token obtained")
        
        # Encode token for ODBC
        token_bytes = token.encode('utf-16-le')
        token_struct = struct.pack(f'<I{len(token_bytes)}s', len(token_bytes), token_bytes)
        
        # Connection string with token
        conn_string = (
            f'Driver={{ODBC Driver 18 for SQL Server}};'
            f'Server=tcp:{SERVER},1433;'
            f'Database={DATABASE};'
            f'Encrypt=yes;'
            f'TrustServerCertificate=no;'
            f'Connection Timeout=30;'
        )
        
        print("\nConnecting to database...")
        conn = pyodbc.connect(conn_string, attrs_before={1256: token_struct})
        cursor = conn.cursor()
        
        print("✓ Connected successfully!")
        
        # Test query
        cursor.execute("SELECT @@VERSION")
        version = cursor.fetchone()[0]
        print(f"\n✓ SQL Server Version:")
        print(f"  {version[:80]}...")
        
        # Check if tables exist
        cursor.execute("""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_SCHEMA = 'dbo'
        """)
        table_count = cursor.fetchone()[0]
        print(f"\n✓ Existing tables in dbo schema: {table_count}")
        
        if table_count > 0:
            cursor.execute("""
                SELECT TABLE_NAME 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_SCHEMA = 'dbo'
                ORDER BY TABLE_NAME
            """)
            print("\nExisting tables:")
            for row in cursor.fetchall():
                print(f"  - {row[0]}")
        
        conn.close()
        
        print("\n" + "=" * 60)
        print("✓ CONNECTION TEST SUCCESSFUL!")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n✗ Connection failed: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure you're logged in to Azure CLI: az login")
        print("2. Verify your account has access to the database")
        print("3. Check firewall rules allow your IP")
        print("4. Ensure ODBC Driver 18 for SQL Server is installed")
        return False

if __name__ == "__main__":
    success = test_connection()
    exit(0 if success else 1)
