"""
Azure Function App for Synthetic Data Generation
Generates 500 new records every 24 hours for Azure SQL Database
"""

import azure.functions as func
import logging

app = func.FunctionApp()

@app.timer_trigger(
    schedule="0 0 0 * * *",  # Runs every day at midnight UTC (CRON: seconds minutes hours day month dayOfWeek)
    arg_name="myTimer", 
    run_on_startup=False,
    use_monitor=True
) 
def daily_data_generator(myTimer: func.TimerRequest) -> None:
    """
    Timer trigger function that runs every 24 hours to generate synthetic data.
    Schedule: 0 0 0 * * * = Every day at midnight UTC
    """
    import os
    import pyodbc
    import random
    import struct
    from datetime import datetime, timedelta
    from faker import Faker
    from azure.identity import DefaultAzureCredential
    
    if myTimer.past_due:
        logging.info('The timer is past due!')
    
    logging.info('Starting synthetic data generation...')
    logging.info(f'Python timer trigger function ran at: {datetime.utcnow()}')
    
    fake = Faker()
    
    # Database connection configuration from environment variables
    SERVER = os.environ.get('SQL_SERVER', 'aiagentsdemo.database.windows.net')
    DATABASE = os.environ.get('SQL_DATABASE')
    AUTH_TYPE = os.environ.get('SQL_AUTH_TYPE', 'AzureAD')
    
    if not DATABASE:
        logging.error('Missing required environment variable: SQL_DATABASE')
        return
    
    def get_azure_ad_token():
        """Get Azure AD access token for SQL Database"""
        credential = DefaultAzureCredential()
        token = credential.get_token("https://database.windows.net/.default")
        return token.token
    
    # Connection string
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
        attrs_before = {1256: token_struct}
    else:
        # SQL authentication (fallback)
        USERNAME = os.environ.get('SQL_USERNAME')
        PASSWORD = os.environ.get('SQL_PASSWORD')
        if not all([USERNAME, PASSWORD]):
            logging.error('Missing required environment variables: SQL_USERNAME or SQL_PASSWORD')
            return
        
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
        attrs_before = None
    
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
    
    try:
        # Connect to database
        logging.info(f'Connecting to database: {DATABASE}')
        if attrs_before:
            conn = pyodbc.connect(conn_string, attrs_before=attrs_before)
        else:
            conn = pyodbc.connect(conn_string)
        cursor = conn.cursor()
        logging.info('Connected to database successfully')
        
        # Distribution of 500 records across tables
        # Products: 50, Customers: 100, Orders: 200, OrderItems: ~400-600 (2-3 per order)
        products_to_create = 50
        customers_to_create = 100
        orders_to_create = 200
        
        products_created = 0
        customers_created = 0
        orders_created = 0
        items_created = 0
        
        # Generate Products
        logging.info(f'Generating {products_to_create} new products...')
        for i in range(products_to_create):
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
                logging.warning(f'Error inserting product: {e}')
        
        conn.commit()
        logging.info(f'✓ Created {products_created} products')
        
        # Generate Customers
        logging.info(f'Generating {customers_to_create} new customers...')
        for i in range(customers_to_create):
            first_name = fake.first_name()
            last_name = fake.last_name()
            email = f"{first_name.lower()}.{last_name.lower()}{random.randint(1,9999)}@{fake.free_email_domain()}"
            phone = fake.numerify(text='###-###-####')  # Generate simple 10-digit phone
            address = fake.street_address()
            city = fake.city()
            state = fake.state_abbr()
            zipcode = fake.zipcode()
            customer_since = datetime.utcnow() - timedelta(days=random.randint(1, 365))
            
            try:
                cursor.execute("""
                    INSERT INTO dbo.Customers 
                    (FirstName, LastName, Email, PhoneNumber, Address, City, State, ZipCode, CustomerSince)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, first_name, last_name, email, phone, address, city, state, zipcode, customer_since)
                customers_created += 1
            except Exception as e:
                logging.warning(f'Error inserting customer: {e}')
        
        conn.commit()
        logging.info(f'✓ Created {customers_created} customers')
        
        # Get customer and product IDs for orders
        cursor.execute("SELECT CustomerID FROM dbo.Customers")
        customer_ids = [row[0] for row in cursor.fetchall()]
        
        cursor.execute("SELECT ProductID, Price FROM dbo.Products")
        products = {row[0]: float(row[1]) for row in cursor.fetchall()}  # Convert Decimal to float
        product_ids = list(products.keys())
        
        # Generate Orders and OrderItems
        logging.info(f'Generating {orders_to_create} new orders with items...')
        for i in range(orders_to_create):
            customer_id = random.choice(customer_ids)
            order_date = datetime.utcnow() - timedelta(days=random.randint(0, 30))
            status = random.choice(ORDER_STATUSES)
            payment_method = random.choice(PAYMENT_METHODS)
            
            shipping_address = fake.street_address()
            shipping_city = fake.city()
            shipping_state = fake.state_abbr()
            shipping_zip = fake.zipcode()
            
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
                
                # Generate 2-3 order items per order
                num_items = random.randint(2, 3)
                total_amount = 0
                
                for _ in range(num_items):
                    product_id = random.choice(product_ids)
                    quantity = random.randint(1, 5)
                    unit_price = float(products[product_id])  # Convert Decimal to float
                    discount = random.choice([0, 0, 0, 5, 10, 15, 20])
                    
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
                logging.warning(f'Error inserting order: {e}')
        
        conn.commit()
        logging.info(f'✓ Created {orders_created} orders')
        logging.info(f'✓ Created {items_created} order items')
        
        # Get current totals
        cursor.execute("SELECT COUNT(*) FROM dbo.Products")
        total_products = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM dbo.Customers")
        total_customers = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM dbo.Orders")
        total_orders = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM dbo.OrderItems")
        total_items = cursor.fetchone()[0]
        
        conn.close()
        
        total_created = products_created + customers_created + orders_created + items_created
        
        logging.info('=' * 60)
        logging.info('SYNTHETIC DATA GENERATION COMPLETE!')
        logging.info('=' * 60)
        logging.info(f'Records Created This Run: {total_created}')
        logging.info(f'  - Products:     {products_created}')
        logging.info(f'  - Customers:    {customers_created}')
        logging.info(f'  - Orders:       {orders_created}')
        logging.info(f'  - Order Items:  {items_created}')
        logging.info('-' * 60)
        logging.info('Total Records in Database:')
        logging.info(f'  - Products:     {total_products}')
        logging.info(f'  - Customers:    {total_customers}')
        logging.info(f'  - Orders:       {total_orders}')
        logging.info(f'  - Order Items:  {total_items}')
        logging.info('=' * 60)
        
    except Exception as e:
        logging.error(f'Error in data generation: {e}', exc_info=True)
        raise
