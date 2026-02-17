"""
Script to generate initial synthetic data for Azure SQL Database
Database: <your-sql-server>.database.windows.net

This script creates initial realistic data for:
- Products (100 records)
- Customers (200 records)
- Orders (300 records)
- OrderItems (600+ records)
"""

import os
import pyodbc
import random
import struct
from datetime import datetime, timedelta
from faker import Faker
from azure.identity import DefaultAzureCredential

fake = Faker()

# Database connection configuration
SERVER = os.getenv('SQL_SERVER', '<your-sql-server>.database.windows.net')
DATABASE = os.getenv('SQL_DATABASE', 'aiagentsdb')
AUTH_TYPE = os.getenv('SQL_AUTH_TYPE', 'AzureAD')

def get_azure_ad_token():
    """Get Azure AD access token for SQL Database"""
    credential = DefaultAzureCredential()
    token = credential.get_token("https://database.windows.net/.default")
    return token.token

# Product templates per category
PRODUCT_TEMPLATES = {
    1: ['Laptop', 'Smartphone', 'Tablet', 'Headphones', 'Smartwatch', 'Camera', 'Monitor', 'Keyboard', 'Mouse', 'Speaker'],
    2: ['T-Shirt', 'Jeans', 'Dress', 'Jacket', 'Sneakers', 'Sweater', 'Shorts', 'Skirt', 'Coat', 'Boots'],
    3: ['Lamp', 'Vase', 'Curtains', 'Rug', 'Plant Pot', 'Chair', 'Table', 'Mirror', 'Shelf', 'Cushion'],
    4: ['Running Shoes', 'Yoga Mat', 'Dumbbell Set', 'Tennis Racket', 'Backpack', 'Water Bottle', 'Bicycle', 'Tent', 'Sleeping Bag', 'Hiking Boots'],
    5: ['Fiction Novel', 'Cookbook', 'Biography', 'Self-Help Book', 'Children\'s Book', 'Textbook', 'Magazine', 'Comic Book', 'Dictionary', 'Atlas'],
    6: ['Board Game', 'Puzzle', 'Action Figure', 'Doll', 'Building Blocks', 'Video Game', 'Card Game', 'Remote Control Car', 'Stuffed Animal', 'Art Set'],
    7: ['Face Cream', 'Shampoo', 'Vitamins', 'Perfume', 'Makeup Kit', 'Soap', 'Toothpaste', 'Hair Dryer', 'Electric Shaver', 'Moisturizer'],
    8: ['Coffee Beans', 'Tea Set', 'Chocolate Box', 'Olive Oil', 'Pasta', 'Wine', 'Cheese', 'Spices', 'Cookies', 'Energy Bars'],
    9: ['Car Mats', 'Air Freshener', 'Phone Mount', 'Dash Cam', 'Tire Gauge', 'Car Cover', 'Jump Starter', 'Wiper Blades', 'Seat Covers', 'Tool Kit'],
    10: ['Notebook', 'Pens', 'Stapler', 'Desk Organizer', 'File Folders', 'Calculator', 'Marker Set', 'Paper Clips', 'Scissors', 'Tape Dispenser']
}

ORDER_STATUSES = ['Pending', 'Processing', 'Shipped', 'Delivered', 'Cancelled']
PAYMENT_METHODS = ['Credit Card', 'Debit Card', 'PayPal', 'Apple Pay', 'Google Pay', 'Bank Transfer']


def get_connection():
    """Create and return database connection"""
    try:
        if AUTH_TYPE == 'AzureAD':
            # Azure AD authentication
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
        else:
            # SQL authentication (fallback)
            USERNAME = os.getenv('SQL_USERNAME')
            PASSWORD = os.getenv('SQL_PASSWORD')
            conn_string = (
                f'Driver={{ODBC Driver 18 for SQL Server}};'
                f'Server=tcp:{SERVER},1433;'
                f'Database={DATABASE};'
                f'Uid={USERNAME};'
                f'Pwd={PASSWORD};'
                f'Encrypt=yes;'
                f'TrustServerCertificate=no;'
                f'Connection Timeout=30;'
            )
            return pyodbc.connect(conn_string)
    except Exception as e:
        print(f"Error connecting to database: {e}")
        raise


def generate_products(conn, count=100):
    """Generate synthetic product data"""
    cursor = conn.cursor()
    print(f"Generating {count} products...")
    
    products_created = 0
    for i in range(count):
        category_id = random.randint(1, 10)
        product_base = random.choice(PRODUCT_TEMPLATES[category_id])
        brand = fake.company()
        product_name = f"{brand} {product_base}"
        price = round(random.uniform(9.99, 999.99), 2)
        stock = random.randint(0, 500)
        sku = f"SKU{fake.bothify(text='???-#####')}"
        description = fake.text(max_nb_chars=200)
        
        try:
            cursor.execute("""
                INSERT INTO dbo.Products (ProductName, CategoryID, Price, StockQuantity, Description, SKU)
                VALUES (?, ?, ?, ?, ?, ?)
            """, product_name, category_id, price, stock, description, sku)
            products_created += 1
        except Exception as e:
            print(f"Error inserting product: {e}")
    
    conn.commit()
    print(f"✓ Created {products_created} products")


def generate_customers(conn, count=200):
    """Generate synthetic customer data"""
    cursor = conn.cursor()
    print(f"Generating {count} customers...")
    
    customers_created = 0
    for i in range(count):
        first_name = fake.first_name()
        last_name = fake.last_name()
        email = f"{first_name.lower()}.{last_name.lower()}{random.randint(1,9999)}@{fake.free_email_domain()}"
        phone = fake.numerify(text='###-###-####')  # Generate simple 10-digit phone
        address = fake.street_address()
        city = fake.city()
        state = fake.state_abbr()
        zipcode = fake.zipcode()
        customer_since = fake.date_time_between(start_date='-5y', end_date='now')
        
        try:
            cursor.execute("""
                INSERT INTO dbo.Customers 
                (FirstName, LastName, Email, PhoneNumber, Address, City, State, ZipCode, CustomerSince)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, first_name, last_name, email, phone, address, city, state, zipcode, customer_since)
            customers_created += 1
        except Exception as e:
            print(f"Error inserting customer: {e}")
    
    conn.commit()
    print(f"✓ Created {customers_created} customers")


def generate_orders_and_items(conn, order_count=300):
    """Generate synthetic orders and order items"""
    cursor = conn.cursor()
    
    # Get customer IDs
    cursor.execute("SELECT CustomerID FROM dbo.Customers")
    customer_ids = [row[0] for row in cursor.fetchall()]
    
    # Get product info
    cursor.execute("SELECT ProductID, Price FROM dbo.Products")
    products = {row[0]: float(row[1]) for row in cursor.fetchall()}  # Convert Decimal to float
    product_ids = list(products.keys())
    
    print(f"Generating {order_count} orders with items...")
    
    orders_created = 0
    items_created = 0
    
    for i in range(order_count):
        customer_id = random.choice(customer_ids)
        order_date = fake.date_time_between(start_date='-1y', end_date='now')
        status = random.choice(ORDER_STATUSES)
        payment_method = random.choice(PAYMENT_METHODS)
        
        # Shipping address
        shipping_address = fake.street_address()
        shipping_city = fake.city()
        shipping_state = fake.state_abbr()
        shipping_zip = fake.zipcode()
        
        # Shipped date (if applicable)
        shipped_date = None
        if status in ['Shipped', 'Delivered']:
            shipped_date = order_date + timedelta(days=random.randint(1, 5))
        
        try:
            # Insert order
            cursor.execute("""
                INSERT INTO dbo.Orders 
                (CustomerID, OrderDate, ShippedDate, OrderStatus, TotalAmount, 
                 ShippingAddress, ShippingCity, ShippingState, ShippingZipCode, PaymentMethod)
                VALUES (?, ?, ?, ?, 0, ?, ?, ?, ?, ?)
            """, customer_id, order_date, shipped_date, status, 
               shipping_address, shipping_city, shipping_state, shipping_zip, payment_method)
            
            # Get the order ID
            cursor.execute("SELECT @@IDENTITY")
            order_id = cursor.fetchone()[0]
            orders_created += 1
            
            # Generate 1-5 order items
            num_items = random.randint(1, 5)
            total_amount = 0
            
            for _ in range(num_items):
                product_id = random.choice(product_ids)
                quantity = random.randint(1, 5)
                unit_price = float(products[product_id])  # Convert Decimal to float
                discount = random.choice([0, 0, 0, 5, 10, 15, 20])  # Most items have no discount
                
                cursor.execute("""
                    INSERT INTO dbo.OrderItems 
                    (OrderID, ProductID, Quantity, UnitPrice, Discount)
                    VALUES (?, ?, ?, ?, ?)
                """, order_id, product_id, quantity, unit_price, discount)
                
                line_total = quantity * unit_price * (1 - discount/100)
                total_amount += float(line_total)
                items_created += 1
            
            # Update order total
            cursor.execute("""
                UPDATE dbo.Orders 
                SET TotalAmount = ? 
                WHERE OrderID = ?
            """, round(total_amount, 2), order_id)
            
        except Exception as e:
            print(f"Error inserting order: {e}")
    
    conn.commit()
    print(f"✓ Created {orders_created} orders")
    print(f"✓ Created {items_created} order items")


def main():
    """Main execution function"""
    print("=" * 60)
    print("Synthetic Data Generator for Azure SQL Database")
    print("=" * 60)
    print(f"Target Server: {SERVER}")
    print(f"Target Database: {DATABASE}")
    print("=" * 60)
    
    try:
        # Connect to database
        print("\nConnecting to database...")
        conn = get_connection()
        print("✓ Connected successfully\n")
        
        # Generate data
        generate_products(conn, 100)
        generate_customers(conn, 200)
        generate_orders_and_items(conn, 300)
        
        # Summary
        cursor = conn.cursor()
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
        
        print("\n" + "=" * 60)
        print("DATA GENERATION COMPLETE!")
        print("=" * 60)
        print(f"Categories:   {cat_count}")
        print(f"Products:     {prod_count}")
        print(f"Customers:    {cust_count}")
        print(f"Orders:       {order_count}")
        print(f"Order Items:  {item_count}")
        print("=" * 60)
        
        conn.close()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
