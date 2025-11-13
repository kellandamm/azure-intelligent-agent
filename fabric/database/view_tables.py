"""
View all tables and data in the Azure SQL Database
Database: aiagentsdemo.database.windows.net/aiagentsdb
"""

import os
import pyodbc
import struct
from azure.identity import DefaultAzureCredential
from datetime import datetime

# Database connection configuration
SERVER = os.getenv('SQL_SERVER', 'aiagentsdemo.database.windows.net')
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

def print_separator(char="=", length=100):
    print(char * length)

def view_categories(cursor):
    """View all categories"""
    print("\n📁 CATEGORIES TABLE")
    print_separator()
    cursor.execute("SELECT * FROM dbo.Categories ORDER BY CategoryID")
    rows = cursor.fetchall()
    
    print(f"{'ID':<5} {'Category Name':<30} {'Description':<60}")
    print_separator("-")
    for row in rows:
        print(f"{row.CategoryID:<5} {row.CategoryName:<30} {row.Description or '':<60}")
    print(f"\nTotal Categories: {len(rows)}")

def view_products(cursor, limit=20):
    """View products"""
    print("\n📦 PRODUCTS TABLE (Top 20)")
    print_separator()
    cursor.execute(f"""
        SELECT TOP {limit} p.ProductID, p.ProductName, c.CategoryName, p.Price, 
               p.StockQuantity, p.SKU, p.CreatedDate
        FROM dbo.Products p
        JOIN dbo.Categories c ON p.CategoryID = c.CategoryID
        ORDER BY p.CreatedDate DESC
    """)
    rows = cursor.fetchall()
    
    print(f"{'ID':<5} {'Product Name':<35} {'Category':<20} {'Price':<10} {'Stock':<8} {'SKU':<15}")
    print_separator("-")
    for row in rows:
        price = f"${row.Price:,.2f}"
        print(f"{row.ProductID:<5} {row.ProductName[:34]:<35} {row.CategoryName[:19]:<20} {price:<10} {row.StockQuantity:<8} {row.SKU:<15}")
    
    cursor.execute("SELECT COUNT(*) FROM dbo.Products")
    total = cursor.fetchone()[0]
    print(f"\nTotal Products: {total} (showing top {limit})")

def view_customers(cursor, limit=20):
    """View customers"""
    print("\n👥 CUSTOMERS TABLE (Top 20)")
    print_separator()
    cursor.execute(f"""
        SELECT TOP {limit} CustomerID, FirstName, LastName, Email, PhoneNumber, 
               City, State, CustomerSince
        FROM dbo.Customers
        ORDER BY CustomerSince DESC
    """)
    rows = cursor.fetchall()
    
    print(f"{'ID':<5} {'Name':<30} {'Email':<40} {'Phone':<15} {'Location':<25}")
    print_separator("-")
    for row in rows:
        name = f"{row.FirstName} {row.LastName}"
        location = f"{row.City}, {row.State}" if row.City else ""
        print(f"{row.CustomerID:<5} {name[:29]:<30} {row.Email[:39]:<40} {row.PhoneNumber or '':<15} {location[:24]:<25}")
    
    cursor.execute("SELECT COUNT(*) FROM dbo.Customers")
    total = cursor.fetchone()[0]
    print(f"\nTotal Customers: {total} (showing top {limit})")

def view_orders(cursor, limit=20):
    """View orders"""
    print("\n🛒 ORDERS TABLE (Top 20)")
    print_separator()
    cursor.execute(f"""
        SELECT TOP {limit} o.OrderID, o.CustomerID, 
               c.FirstName + ' ' + c.LastName as CustomerName,
               o.OrderDate, o.OrderStatus, o.TotalAmount, o.PaymentMethod
        FROM dbo.Orders o
        JOIN dbo.Customers c ON o.CustomerID = c.CustomerID
        ORDER BY o.OrderDate DESC
    """)
    rows = cursor.fetchall()
    
    print(f"{'ID':<6} {'Customer':<30} {'Order Date':<20} {'Status':<12} {'Total':<12} {'Payment':<15}")
    print_separator("-")
    for row in rows:
        order_date = row.OrderDate.strftime("%Y-%m-%d %H:%M") if row.OrderDate else ""
        total = f"${row.TotalAmount:,.2f}"
        print(f"{row.OrderID:<6} {row.CustomerName[:29]:<30} {order_date:<20} {row.OrderStatus:<12} {total:<12} {row.PaymentMethod or '':<15}")
    
    cursor.execute("SELECT COUNT(*) FROM dbo.Orders")
    total = cursor.fetchone()[0]
    cursor.execute("SELECT SUM(TotalAmount) FROM dbo.Orders")
    total_revenue = cursor.fetchone()[0]
    print(f"\nTotal Orders: {total} (showing top {limit})")
    print(f"Total Revenue: ${total_revenue:,.2f}" if total_revenue else "Total Revenue: $0.00")

def view_order_items(cursor, limit=20):
    """View order items"""
    print("\n📝 ORDER ITEMS TABLE (Top 20)")
    print_separator()
    cursor.execute(f"""
        SELECT TOP {limit} oi.OrderItemID, oi.OrderID, p.ProductName, 
               oi.Quantity, oi.UnitPrice, oi.Discount,
               (oi.Quantity * oi.UnitPrice * (1 - oi.Discount/100)) as LineTotal
        FROM dbo.OrderItems oi
        JOIN dbo.Products p ON oi.ProductID = p.ProductID
        ORDER BY oi.OrderItemID DESC
    """)
    rows = cursor.fetchall()
    
    print(f"{'Item ID':<8} {'Order ID':<10} {'Product':<40} {'Qty':<5} {'Price':<10} {'Disc%':<7} {'Total':<12}")
    print_separator("-")
    for row in rows:
        price = f"${row.UnitPrice:,.2f}"
        total = f"${row.LineTotal:,.2f}"
        print(f"{row.OrderItemID:<8} {row.OrderID:<10} {row.ProductName[:39]:<40} {row.Quantity:<5} {price:<10} {row.Discount:<7} {total:<12}")
    
    cursor.execute("SELECT COUNT(*) FROM dbo.OrderItems")
    total = cursor.fetchone()[0]
    print(f"\nTotal Order Items: {total} (showing top {limit})")

def view_summary(cursor):
    """View database summary"""
    print("\n📊 DATABASE SUMMARY")
    print_separator()
    
    # Get counts
    cursor.execute("SELECT COUNT(*) FROM dbo.Categories")
    cat_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM dbo.Products")
    prod_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM dbo.Customers")
    cust_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM dbo.Orders")
    order_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM dbo.OrderItems")
    item_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT SUM(TotalAmount) FROM dbo.Orders")
    total_revenue = cursor.fetchone()[0] or 0
    
    cursor.execute("SELECT AVG(TotalAmount) FROM dbo.Orders")
    avg_order = cursor.fetchone()[0] or 0
    
    cursor.execute("""
        SELECT TOP 1 c.CategoryName, COUNT(*) as ProductCount
        FROM dbo.Products p
        JOIN dbo.Categories c ON p.CategoryID = c.CategoryID
        GROUP BY c.CategoryName
        ORDER BY COUNT(*) DESC
    """)
    top_category = cursor.fetchone()
    
    cursor.execute("""
        SELECT OrderStatus, COUNT(*) as Count
        FROM dbo.Orders
        GROUP BY OrderStatus
        ORDER BY COUNT(*) DESC
    """)
    order_statuses = cursor.fetchall()
    
    print(f"{'Metric':<30} {'Value':<20}")
    print_separator("-")
    print(f"{'Total Categories':<30} {cat_count:<20,}")
    print(f"{'Total Products':<30} {prod_count:<20,}")
    print(f"{'Total Customers':<30} {cust_count:<20,}")
    print(f"{'Total Orders':<30} {order_count:<20,}")
    print(f"{'Total Order Items':<30} {item_count:<20,}")
    print(f"{'Total Revenue':<30} ${total_revenue:<19,.2f}")
    print(f"{'Average Order Value':<30} ${avg_order:<19,.2f}")
    if top_category:
        print(f"{'Top Category':<30} {top_category.CategoryName} ({top_category.ProductCount} products)")
    
    print(f"\n{'Order Status Distribution:':<30}")
    print_separator("-")
    for status in order_statuses:
        print(f"  {status.OrderStatus:<28} {status.Count:<20,}")

def main():
    """Main execution function"""
    print("=" * 100)
    print(" " * 30 + "AZURE SQL DATABASE - TABLE VIEWER")
    print("=" * 100)
    print(f"Server:   {SERVER}")
    print(f"Database: {DATABASE}")
    print(f"Date:     {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 100)
    
    try:
        # Connect to database
        print("\nConnecting to database...")
        conn = get_connection()
        cursor = conn.cursor()
        print("✓ Connected successfully")
        
        # View all tables
        view_summary(cursor)
        view_categories(cursor)
        view_products(cursor, limit=20)
        view_customers(cursor, limit=20)
        view_orders(cursor, limit=20)
        view_order_items(cursor, limit=20)
        
        print("\n" + "=" * 100)
        print("✓ Database query completed successfully!")
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
