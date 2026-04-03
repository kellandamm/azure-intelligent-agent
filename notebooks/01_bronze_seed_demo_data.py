# Fabric notebook source: Bronze seed demo data
# Purpose: land raw demo entities in a Bronze Lakehouse.

from pyspark.sql import functions as F
from datetime import datetime, timedelta
import random

CONFIG = {
    'NUM_CUSTOMERS': 5000,
    'NUM_PRODUCTS': 500,
    'NUM_ORDERS': 25000,
    'NUM_SUPPORT_TICKETS': 2000,
    'NUM_OPPORTUNITIES': 1500,
    'NUM_INTERACTIONS': 10000,
    'DATE_RANGE_DAYS': 365
}

print('Starting Bronze seed generation')

sales_reps = ['John Smith', 'Sarah Johnson', 'Mike Williams', 'Emily Davis', 'Chris Brown']
first_names = ['James', 'Mary', 'John', 'Patricia', 'Robert', 'Jennifer', 'Michael', 'Linda', 'William', 'Elizabeth', 'David', 'Barbara', 'Richard', 'Susan', 'Joseph', 'Jessica', 'Thomas', 'Sarah', 'Charles', 'Karen']
last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson', 'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin']
state_rows = [
    ('CA', 'California', 'West', 'Pacific', 39500000, 'Sacramento'),
    ('TX', 'Texas', 'South', 'Southwest', 29000000, 'Austin'),
    ('FL', 'Florida', 'South', 'Southeast', 21500000, 'Tallahassee'),
    ('NY', 'New York', 'Northeast', 'Mid-Atlantic', 19500000, 'Albany'),
    ('PA', 'Pennsylvania', 'Northeast', 'Mid-Atlantic', 12800000, 'Harrisburg'),
    ('IL', 'Illinois', 'Midwest', 'Great Lakes', 12700000, 'Springfield'),
    ('OH', 'Ohio', 'Midwest', 'Great Lakes', 11700000, 'Columbus'),
    ('GA', 'Georgia', 'South', 'Southeast', 10600000, 'Atlanta'),
    ('NC', 'North Carolina', 'South', 'Southeast', 10400000, 'Raleigh'),
    ('MI', 'Michigan', 'Midwest', 'Great Lakes', 10000000, 'Lansing'),
    ('NJ', 'New Jersey', 'Northeast', 'Mid-Atlantic', 9300000, 'Trenton'),
    ('VA', 'Virginia', 'South', 'Southeast', 8600000, 'Richmond'),
    ('WA', 'Washington', 'West', 'Pacific', 7700000, 'Olympia'),
    ('AZ', 'Arizona', 'West', 'Southwest', 7300000, 'Phoenix'),
    ('MA', 'Massachusetts', 'Northeast', 'New England', 6900000, 'Boston'),
    ('TN', 'Tennessee', 'South', 'Southeast', 6900000, 'Nashville'),
    ('IN', 'Indiana', 'Midwest', 'Great Lakes', 6800000, 'Indianapolis'),
    ('MD', 'Maryland', 'South', 'Mid-Atlantic', 6200000, 'Annapolis'),
    ('MO', 'Missouri', 'Midwest', 'Great Plains', 6200000, 'Jefferson City'),
    ('WI', 'Wisconsin', 'Midwest', 'Great Lakes', 5900000, 'Madison')
]

category_rows = [
    ('Electronics', 'Electronic devices, computers, and accessories', 'Tech', True, 0.35),
    ('Clothing', 'Apparel and fashion items', 'Retail', True, 0.60),
    ('Home & Garden', 'Home improvement and outdoor living', 'Retail', True, 0.45),
    ('Sports & Outdoors', 'Sporting goods and outdoor equipment', 'Retail', True, 0.40),
    ('Books & Media', 'Books, movies, and digital content', 'Media', True, 0.25),
    ('Toys & Games', 'Toys, games, and entertainment', 'Retail', True, 0.50),
    ('Food & Beverage', 'Groceries and consumables', 'Grocery', True, 0.70),
    ('Health & Beauty', 'Health products and cosmetics', 'Health', True, 0.55),
    ('Automotive', 'Car parts and accessories', 'Automotive', True, 0.30),
    ('Office Supplies', 'Business and office products', 'B2B', True, 0.40),
    ('Pet Supplies', 'Pet food, toys, and accessories', 'Specialty', True, 0.45),
    ('Jewelry', 'Jewelry and watches', 'Luxury', True, 0.15),
    ('Tools & Hardware', 'Power tools and hardware', 'Industrial', True, 0.35),
    ('Baby Products', 'Baby care and nursery items', 'Specialty', True, 0.50),
    ('Furniture', 'Home and office furniture', 'Retail', True, 0.25)
]

product_types = {
    'Electronics': ['Laptop', 'Smartphone', 'Tablet', 'Headphones', 'Smart Watch', 'Monitor', 'Keyboard', 'Mouse', 'Speaker', 'Camera'],
    'Clothing': ['T-Shirt', 'Jeans', 'Dress', 'Jacket', 'Sneakers', 'Boots', 'Sweater', 'Shorts', 'Skirt', 'Coat'],
    'Home & Garden': ['Coffee Maker', 'Blender', 'Vacuum', 'Garden Hose', 'Patio Set', 'Lawn Mower', 'Grill', 'Tool Set'],
    'Sports & Outdoors': ['Yoga Mat', 'Dumbbells', 'Bicycle', 'Tent', 'Sleeping Bag', 'Running Shoes', 'Backpack'],
    'Books & Media': ['Fiction Book', 'Textbook', 'Magazine', 'DVD', 'Blu-ray', 'Audiobook', 'eBook'],
    'Toys & Games': ['Action Figure', 'Board Game', 'Puzzle', 'LEGO Set', 'Doll', 'Video Game', 'RC Car'],
    'Food & Beverage': ['Coffee Beans', 'Tea', 'Snack Bar', 'Protein Powder', 'Energy Drink', 'Cereal'],
    'Health & Beauty': ['Shampoo', 'Moisturizer', 'Vitamins', 'Face Mask', 'Perfume', 'Toothpaste'],
    'Automotive': ['Motor Oil', 'Car Wax', 'Air Freshener', 'Floor Mats', 'Battery', 'Tire'],
    'Office Supplies': ['Printer Paper', 'Pen Set', 'Notebook', 'Desk Organizer', 'Calculator', 'Stapler'],
    'Pet Supplies': ['Dog Food', 'Cat Litter', 'Pet Toy', 'Leash', 'Pet Bed', 'Treats'],
    'Jewelry': ['Necklace', 'Ring', 'Bracelet', 'Earrings', 'Watch', 'Pendant'],
    'Tools & Hardware': ['Drill', 'Hammer', 'Wrench Set', 'Screwdriver', 'Tape Measure', 'Saw'],
    'Baby Products': ['Diapers', 'Baby Formula', 'Stroller', 'Car Seat', 'Baby Monitor', 'Crib'],
    'Furniture': ['Desk', 'Chair', 'Sofa', 'Bed Frame', 'Bookshelf', 'Table']
}
brands = ['ProTech', 'Elite', 'Premium', 'Classic', 'Deluxe', 'Essential', 'Ultra', 'Prime', 'Signature', 'Professional']

bronze_geography = spark.createDataFrame(state_rows, ['state_code', 'state_name', 'region', 'division', 'population', 'capital'])
bronze_geography.write.format('delta').mode('overwrite').saveAsTable('bronze_geography_raw')

bronze_categories = spark.createDataFrame(category_rows, ['category_name', 'description', 'department', 'is_active', 'margin_pct'])
bronze_categories.write.format('delta').mode('overwrite').saveAsTable('bronze_categories_raw')

products = []
product_id = 1
for category, items in product_types.items():
    for item in items:
        for brand in random.sample(brands, 3):
            products.append((product_id, f'{brand} {item}', category, brand, round(random.uniform(9.99, 999.99), 2), round(random.uniform(5.0, 500.0), 2), round(random.uniform(1, 100), 1), f'SKU-{product_id:05d}', str(random.randint(100000000000, 999999999999)), random.choice([True, True, True, False]), random.randint(0, 500), random.randint(10, 50), random.choice(['Supplier A', 'Supplier B', 'Supplier C', 'Supplier D']), random.randint(1, 30), round(random.uniform(2.5, 5.0), 1), random.randint(0, 1000)))
            product_id += 1
            if product_id > CONFIG['NUM_PRODUCTS']:
                break
        if product_id > CONFIG['NUM_PRODUCTS']:
            break
    if product_id > CONFIG['NUM_PRODUCTS']:
        break
spark.createDataFrame(products, ['product_id','product_name','category_name','brand','base_price','cost','weight_oz','sku','upc','is_active','stock_quantity','reorder_level','supplier','lead_time_days','rating','review_count']).write.format('delta').mode('overwrite').saveAsTable('bronze_products_raw')

customers = []
state_codes = [r[0] for r in state_rows]
for i in range(CONFIG['NUM_CUSTOMERS']):
    first = random.choice(first_names)
    last = random.choice(last_names)
    customers.append((i + 1, first, last, f"{first.lower()}.{last.lower()}{random.randint(1,999)}@{random.choice(['gmail.com','yahoo.com','outlook.com','company.com'])}", f"{random.randint(200,999)}-{random.randint(200,999)}-{random.randint(1000,9999)}", random.choice(state_codes), datetime.now() - timedelta(days=random.randint(1, CONFIG['DATE_RANGE_DAYS'])), random.choices(['Enterprise','Business','Professional','Standard'], weights=[0.05,0.15,0.30,0.50])[0], random.choice([5000,10000,25000,50000,100000]), random.choice(['Email','Phone','SMS','Mail']), random.choice([True,True,True,True,False]), random.choice(['Bronze','Silver','Gold','Platinum']), random.choice([True, False])))
spark.createDataFrame(customers, ['customer_id','first_name','last_name','email','phone','state_code','customer_since','account_type','credit_limit','preferred_contact','is_active','loyalty_tier','marketing_consent']).write.format('delta').mode('overwrite').saveAsTable('bronze_customers_raw')

orders = []
order_statuses = ['Pending', 'Processing', 'Shipped', 'Delivered', 'Cancelled', 'Returned']
payment_methods = ['Credit Card', 'Debit Card', 'PayPal', 'Apple Pay', 'Google Pay', 'Bank Transfer']
for i in range(CONFIG['NUM_ORDERS']):
    order_date = datetime.now() - timedelta(days=random.randint(1, CONFIG['DATE_RANGE_DAYS']))
    status = random.choices(order_statuses, weights=[0.05,0.10,0.20,0.50,0.10,0.05])[0]
    shipped_date = order_date + timedelta(days=random.randint(1, 7)) if status in ['Shipped','Delivered','Returned'] else None
    delivered_date = shipped_date + timedelta(days=random.randint(1, 5)) if status == 'Delivered' and shipped_date else None
    orders.append((i + 1, random.randint(1, CONFIG['NUM_CUSTOMERS']), order_date, shipped_date, delivered_date, status, random.choice(payment_methods), round(random.uniform(0, 25), 2), random.choice([None, None, None, 'SAVE10', 'WELCOME', 'FREESHIP']), random.choice(['Website','Mobile App','Phone','In-Store']), random.choice(sales_reps + [None, None])))
spark.createDataFrame(orders, ['order_id','customer_id','order_date','shipped_date','delivered_date','order_status','payment_method','shipping_cost','discount_code','channel','sales_rep']).write.format('delta').mode('overwrite').saveAsTable('bronze_orders_raw')

order_items = []
order_item_id = 1
for order_id in range(1, CONFIG['NUM_ORDERS'] + 1):
    num_items = random.choices([1,2,3,4,5], weights=[0.40,0.30,0.15,0.10,0.05])[0]
    for product_id in random.sample(range(1, CONFIG['NUM_PRODUCTS'] + 1), num_items):
        order_items.append((order_item_id, order_id, product_id, random.choices([1,2,3,4,5], weights=[0.60,0.25,0.10,0.03,0.02])[0], random.choices([0,5,10,15,20,25], weights=[0.70,0.10,0.10,0.05,0.03,0.02])[0]))
        order_item_id += 1
spark.createDataFrame(order_items, ['order_item_id','order_id','product_id','quantity','discount_pct']).write.format('delta').mode('overwrite').saveAsTable('bronze_order_items_raw')

opportunity_stages = ['Lead', 'Qualification', 'Proposal', 'Negotiation', 'Closed Won', 'Closed Lost']
lead_sources = ['Website', 'Referral', 'Cold Call', 'Trade Show', 'Social Media', 'Partner', 'Email Campaign']
prob_map = {'Lead': 10, 'Qualification': 25, 'Proposal': 50, 'Negotiation': 75, 'Closed Won': 100, 'Closed Lost': 0}
opportunities = []
for i in range(CONFIG['NUM_OPPORTUNITIES']):
    stage = random.choices(opportunity_stages, weights=[0.20,0.20,0.20,0.15,0.15,0.10])[0]
    created_date = datetime.now() - timedelta(days=random.randint(1, 180))
    expected_close = created_date + timedelta(days=random.randint(30, 120))
    actual_close = created_date + timedelta(days=random.randint(30, 90)) if stage in ['Closed Won','Closed Lost'] else None
    is_won = True if stage == 'Closed Won' else False if stage == 'Closed Lost' else None
    opportunities.append((i + 1, random.randint(1, CONFIG['NUM_CUSTOMERS']), f'Opportunity-{i+1:05d}', stage, prob_map[stage], round(random.uniform(5000, 250000), 2), round(random.uniform(5000, 250000), 2) if stage == 'Closed Won' else None, expected_close, actual_close, is_won, random.choice(lead_sources), random.choice(sales_reps), created_date, created_date + timedelta(days=random.randint(0, 30))))
spark.createDataFrame(opportunities, ['opportunity_id','customer_id','opportunity_name','stage','probability_pct','estimated_value','actual_value','expected_close_date','actual_close_date','is_won','lead_source','assigned_to','created_date','last_modified']).write.format('delta').mode('overwrite').saveAsTable('bronze_opportunities_raw')

interaction_types = ['Email', 'Phone Call', 'Meeting', 'Demo', 'Follow-up', 'Support Call', 'Survey', 'Webinar']
sentiments = ['Positive', 'Neutral', 'Negative']
interactions = []
for i in range(CONFIG['NUM_INTERACTIONS']):
    interactions.append((i + 1, random.randint(1, CONFIG['NUM_CUSTOMERS']), random.choice(interaction_types), datetime.now() - timedelta(days=random.randint(1, 180)), random.randint(5, 120) if random.random() > 0.3 else None, random.choices(sentiments, weights=[0.60,0.30,0.10])[0], f'Customer interaction notes for record {i+1}', random.choice(sales_reps), random.choice([True, False]), random.choice(['Successful','Needs Follow-up','No Answer','Scheduled Meeting'])))
spark.createDataFrame(interactions, ['interaction_id','customer_id','interaction_type','interaction_date','duration_minutes','sentiment','notes','assigned_to','follow_up_required','outcome']).write.format('delta').mode('overwrite').saveAsTable('bronze_customer_interactions_raw')

priorities = ['Low', 'Medium', 'High', 'Critical']
statuses = ['Open', 'In Progress', 'Waiting on Customer', 'Resolved', 'Closed']
categories = ['Technical Issue', 'Billing', 'Feature Request', 'Bug Report', 'Question', 'Account Access']
tickets = []
for i in range(CONFIG['NUM_SUPPORT_TICKETS']):
    created_date = datetime.now() - timedelta(days=random.randint(1, 90))
    status = random.choices(statuses, weights=[0.10,0.15,0.10,0.35,0.30])[0]
    resolved_date = created_date + timedelta(hours=random.randint(1,72)) if status in ['Resolved','Closed'] else None
    resolution_time_hours = int((resolved_date - created_date).total_seconds() / 3600) if resolved_date else None
    tickets.append((i + 1, random.randint(1, CONFIG['NUM_CUSTOMERS']), f'Support ticket #{i+1}', random.choices(priorities, weights=[0.40,0.35,0.20,0.05])[0], status, random.choice(categories), created_date, resolved_date, resolution_time_hours, random.choice(sales_reps), random.randint(1,5) if status == 'Closed' else None))
spark.createDataFrame(tickets, ['ticket_id','customer_id','subject','priority','status','category','created_date','resolved_date','resolution_time_hours','assigned_to','satisfaction_score']).write.format('delta').mode('overwrite').saveAsTable('bronze_support_tickets_raw')

customer_metrics = []
for customer_id in range(1, CONFIG['NUM_CUSTOMERS'] + 1):
    if random.random() < 0.3:
        customer_metrics.append((customer_id, datetime.now().date(), round(random.uniform(40,100),2), round(random.uniform(30,100),2), round(random.uniform(20,95),1), round(random.uniform(50,100),2), random.choice(['Low','Medium','High']), datetime.now().date() + timedelta(days=random.randint(30,365)), random.randint(-100,100), datetime.now() - timedelta(days=random.randint(0,30))))
spark.createDataFrame(customer_metrics, ['customer_id','measurement_date','health_score','engagement_score','feature_adoption_pct','support_score','renewal_risk','contract_end_date','nps_score','last_login']).write.format('delta').mode('overwrite').saveAsTable('bronze_customer_metrics_raw')

inventory = []
for product_id in range(1, CONFIG['NUM_PRODUCTS'] + 1):
    for days_back in range(0, 30):
        snapshot_date = datetime.now().date() - timedelta(days=days_back)
        inventory.append((product_id, snapshot_date, random.randint(0,500), random.randint(0,50), random.randint(0,450), random.randint(0,200) if random.random() < 0.1 else 0, random.randint(0,3) if random.random() < 0.05 else 0))
spark.createDataFrame(inventory, ['product_id','snapshot_date','quantity_on_hand','quantity_reserved','quantity_available','reorder_quantity','stockout_days']).write.format('delta').mode('overwrite').saveAsTable('bronze_inventory_snapshots_raw')

metadata = [(datetime.now(), 'bronze_seed_complete', 'Bronze raw tables created from demo generator-derived logic')]
spark.createDataFrame(metadata, ['created_at','event_name','event_detail']).write.format('delta').mode('overwrite').saveAsTable('bronze_demo_metadata')

print('Bronze seed complete')
