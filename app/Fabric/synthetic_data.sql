-- ============================================================
-- Synthetic Data for Agent Demo (No Fabric Required)
-- Target: Azure SQL Database (aiagentsdb)
-- Covers: Gold analytic tables + star-schema + operational tables
-- Run as: Azure AD admin in portal Query Editor, or via SSMS
-- Safe to re-run: uses IF NOT EXISTS + TRUNCATE before INSERT
-- ============================================================

PRINT '🚀 Loading synthetic data...';
GO

-- ============================================================
-- SECTION 1: Operational Base Tables
-- (Categories, Products, Customers, Orders, OrderItems)
-- ============================================================

-- Categories
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'Categories' AND schema_id = SCHEMA_ID('dbo'))
BEGIN
    CREATE TABLE dbo.Categories (
        CategoryID      INT IDENTITY(1,1) PRIMARY KEY,
        CategoryName    NVARCHAR(100) NOT NULL,
        Description     NVARCHAR(500),
        CreatedDate     DATETIME2 DEFAULT GETUTCDATE(),
        ModifiedDate    DATETIME2 DEFAULT GETUTCDATE()
    );
    PRINT '✅ Created dbo.Categories';
END
GO

-- Products
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'Products' AND schema_id = SCHEMA_ID('dbo'))
BEGIN
    CREATE TABLE dbo.Products (
        ProductID       INT IDENTITY(1,1) PRIMARY KEY,
        ProductName     NVARCHAR(200) NOT NULL,
        CategoryID      INT REFERENCES dbo.Categories(CategoryID),
        Price           DECIMAL(10,2) NOT NULL,
        StockQuantity   INT DEFAULT 0,
        Description     NVARCHAR(1000),
        SKU             NVARCHAR(50) UNIQUE,
        IsActive        BIT DEFAULT 1,
        CreatedDate     DATETIME2 DEFAULT GETUTCDATE(),
        ModifiedDate    DATETIME2 DEFAULT GETUTCDATE()
    );
    PRINT '✅ Created dbo.Products';
END
GO

-- Customers
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'Customers' AND schema_id = SCHEMA_ID('dbo'))
BEGIN
    CREATE TABLE dbo.Customers (
        CustomerID      INT IDENTITY(1,1) PRIMARY KEY,
        FirstName       NVARCHAR(100) NOT NULL,
        LastName        NVARCHAR(100) NOT NULL,
        Email           NVARCHAR(255) UNIQUE,
        PhoneNumber     NVARCHAR(20),
        Address         NVARCHAR(500),
        City            NVARCHAR(100),
        State           NVARCHAR(50),
        ZipCode         NVARCHAR(20),
        Country         NVARCHAR(100) DEFAULT 'USA',
        CustomerSince   DATETIME2,
        IsActive        BIT DEFAULT 1,
        CreatedDate     DATETIME2 DEFAULT GETUTCDATE(),
        ModifiedDate    DATETIME2 DEFAULT GETUTCDATE()
    );
    PRINT '✅ Created dbo.Customers';
END
GO

-- Orders
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'Orders' AND schema_id = SCHEMA_ID('dbo'))
BEGIN
    CREATE TABLE dbo.Orders (
        OrderID             INT IDENTITY(1,1) PRIMARY KEY,
        CustomerID          INT REFERENCES dbo.Customers(CustomerID),
        OrderDate           DATETIME2,
        ShippedDate         DATETIME2,
        OrderStatus         NVARCHAR(50),
        TotalAmount         DECIMAL(12,2),
        ShippingAddress     NVARCHAR(500),
        ShippingCity        NVARCHAR(100),
        ShippingState       NVARCHAR(50),
        ShippingZipCode     NVARCHAR(20),
        ShippingCountry     NVARCHAR(100),
        PaymentMethod       NVARCHAR(50),
        CreatedDate         DATETIME2 DEFAULT GETUTCDATE(),
        ModifiedDate        DATETIME2 DEFAULT GETUTCDATE()
    );
    PRINT '✅ Created dbo.Orders';
END
GO

-- OrderItems
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'OrderItems' AND schema_id = SCHEMA_ID('dbo'))
BEGIN
    CREATE TABLE dbo.OrderItems (
        OrderItemID     INT IDENTITY(1,1) PRIMARY KEY,
        OrderID         INT REFERENCES dbo.Orders(OrderID),
        ProductID       INT REFERENCES dbo.Products(ProductID),
        Quantity        INT NOT NULL,
        UnitPrice       DECIMAL(10,2) NOT NULL,
        Discount        DECIMAL(5,2) DEFAULT 0,
        LineTotal       AS (Quantity * UnitPrice * (1 - Discount / 100)) PERSISTED,
        CreatedDate     DATETIME2 DEFAULT GETUTCDATE(),
        ModifiedDate    DATETIME2 DEFAULT GETUTCDATE()
    );
    PRINT '✅ Created dbo.OrderItems';
END
GO

-- Seed Categories (skip if already populated)
IF NOT EXISTS (SELECT 1 FROM dbo.Categories)
BEGIN
    SET IDENTITY_INSERT dbo.Categories ON;
    INSERT INTO dbo.Categories (CategoryID, CategoryName, Description) VALUES
        (1, 'Electronics',   'Laptops, tablets, phones, accessories'),
        (2, 'Clothing',      'Apparel and footwear'),
        (3, 'Home & Garden', 'Furniture, decor, and outdoor'),
        (4, 'Sports',        'Athletic gear and equipment'),
        (5, 'Books',         'Printed and digital media'),
        (6, 'Beauty',        'Skincare, hair, and wellness');
    SET IDENTITY_INSERT dbo.Categories OFF;
    PRINT '✅ Seeded Categories';
END
GO

-- Seed Products
IF NOT EXISTS (SELECT 1 FROM dbo.Products)
BEGIN
    SET IDENTITY_INSERT dbo.Products ON;
    INSERT INTO dbo.Products (ProductID, ProductName, CategoryID, Price, StockQuantity, SKU) VALUES
        (1,  'ProBook Laptop 15"',         1, 1249.99, 85,  'ELEC-LP-001'),
        (2,  'UltraTab Pro 11"',           1,  549.99, 120, 'ELEC-TB-001'),
        (3,  'AudioMax Headphones',        1,  179.99, 200, 'ELEC-HP-001'),
        (4,  'SmartWatch Series 4',        1,  299.99, 150, 'ELEC-SW-001'),
        (5,  'CloudPhone X',               1,  899.99, 95,  'ELEC-PH-001'),
        (6,  'AllWeather Jacket',          2,  129.99, 310, 'CLTH-JK-001'),
        (7,  'TrailRunner Sneakers',       2,   89.99, 420, 'CLTH-SN-001'),
        (8,  'ErgoPro Desk Chair',         3,  349.99, 60,  'HOME-CH-001'),
        (9,  'BrewMaster Coffee Maker',    3,   79.99, 180, 'HOME-CM-001'),
        (10, 'FitPro Yoga Mat',            4,   34.99, 500, 'SPRT-YM-001'),
        (11, 'PowerLift Dumbbell Set',     4,  119.99, 75,  'SPRT-DB-001'),
        (12, 'The AI Era (Hardcover)',     5,   28.99, 600, 'BOOK-AI-001'),
        (13, 'GlowSerum Daily Kit',        6,   54.99, 250, 'BEAU-SK-001');
    SET IDENTITY_INSERT dbo.Products OFF;
    PRINT '✅ Seeded Products';
END
GO

-- Seed Customers
IF NOT EXISTS (SELECT 1 FROM dbo.Customers)
BEGIN
    SET IDENTITY_INSERT dbo.Customers ON;
    INSERT INTO dbo.Customers (CustomerID, FirstName, LastName, Email, City, State, ZipCode, CustomerSince, IsActive) VALUES
        (1,  'Alice',   'Johnson',  'alice.johnson@email.com',   'Los Angeles',   'CA', '90001', '2022-01-15', 1),
        (2,  'Bob',     'Smith',    'bob.smith@email.com',       'Houston',       'TX', '77001', '2022-03-20', 1),
        (3,  'Carol',   'Williams', 'carol.williams@email.com',  'Seattle',       'WA', '98101', '2022-06-10', 1),
        (4,  'David',   'Brown',    'david.brown@email.com',     'New York',      'NY', '10001', '2022-08-05', 1),
        (5,  'Eva',     'Davis',    'eva.davis@email.com',       'Miami',         'FL', '33101', '2022-09-18', 1),
        (6,  'Frank',   'Miller',   'frank.miller@email.com',    'Chicago',       'IL', '60601', '2022-11-02', 1),
        (7,  'Grace',   'Wilson',   'grace.wilson@email.com',    'Atlanta',       'GA', '30301', '2023-01-14', 1),
        (8,  'Henry',   'Moore',    'henry.moore@email.com',     'Denver',        'CO', '80201', '2023-03-22', 1),
        (9,  'Iris',    'Taylor',   'iris.taylor@email.com',     'Phoenix',       'AZ', '85001', '2023-05-30', 1),
        (10, 'Jack',    'Anderson', 'jack.anderson@email.com',   'Portland',      'OR', '97201', '2023-07-11', 1),
        (11, 'Karen',   'Thomas',   'karen.thomas@email.com',    'San Diego',     'CA', '92101', '2023-08-19', 1),
        (12, 'Leo',     'Jackson',  'leo.jackson@email.com',     'Austin',        'TX', '78701', '2023-09-25', 1),
        (13, 'Mia',     'White',    'mia.white@email.com',       'Bellevue',      'WA', '98004', '2023-10-31', 1),
        (14, 'Nathan',  'Harris',   'nathan.harris@email.com',   'Brooklyn',      'NY', '11201', '2023-12-07', 1),
        (15, 'Olivia',  'Martin',   'olivia.martin@email.com',   'Orlando',       'FL', '32801', '2024-01-20', 1);
    SET IDENTITY_INSERT dbo.Customers OFF;
    PRINT '✅ Seeded Customers';
END
GO

-- Seed Orders (2025–2026, matching YEAR(GETDATE()) queries)
IF NOT EXISTS (SELECT 1 FROM dbo.Orders)
BEGIN
    SET IDENTITY_INSERT dbo.Orders ON;
    INSERT INTO dbo.Orders (OrderID, CustomerID, OrderDate, ShippedDate, OrderStatus, TotalAmount, ShippingState, PaymentMethod) VALUES
        (1,  1,  '2026-01-05', '2026-01-07', 'Delivered', 1429.98, 'CA', 'Credit Card'),
        (2,  2,  '2026-01-12', '2026-01-14', 'Delivered',  269.98, 'TX', 'PayPal'),
        (3,  3,  '2026-01-18', '2026-01-20', 'Delivered',  729.98, 'WA', 'Credit Card'),
        (4,  4,  '2026-01-25', '2026-01-27', 'Delivered',  179.99, 'NY', 'Debit Card'),
        (5,  5,  '2026-02-02', '2026-02-04', 'Delivered',  899.99, 'FL', 'Credit Card'),
        (6,  6,  '2026-02-09', '2026-02-11', 'Delivered',  219.98, 'IL', 'Credit Card'),
        (7,  7,  '2026-02-14', '2026-02-16', 'Delivered',  349.99, 'GA', 'PayPal'),
        (8,  8,  '2026-02-20', '2026-02-22', 'Delivered',  154.98, 'CO', 'Credit Card'),
        (9,  9,  '2026-02-27', '2026-03-01', 'Delivered', 1249.99, 'AZ', 'Credit Card'),
        (10, 10, '2026-03-05', NULL,          'Processing', 549.99, 'OR', 'Debit Card'),
        (11, 11, '2026-03-08', NULL,          'Shipped',    299.99, 'CA', 'Credit Card'),
        (12, 12, '2026-03-10', NULL,          'Shipped',    209.98, 'TX', 'PayPal'),
        (13, 1,  '2025-10-14', '2025-10-16', 'Delivered',  849.98, 'CA', 'Credit Card'),
        (14, 2,  '2025-10-22', '2025-10-24', 'Delivered',  389.98, 'TX', 'Credit Card'),
        (15, 3,  '2025-11-03', '2025-11-05', 'Delivered',  129.99, 'WA', 'PayPal'),
        (16, 4,  '2025-11-15', '2025-11-17', 'Delivered',  179.99, 'NY', 'Credit Card'),
        (17, 5,  '2025-11-28', '2025-11-30', 'Delivered',  954.97, 'FL', 'Credit Card'),
        (18, 6,  '2025-12-05', '2025-12-07', 'Delivered',  119.99, 'IL', 'Debit Card'),
        (19, 7,  '2025-12-19', '2025-12-21', 'Delivered',  629.98, 'GA', 'Credit Card'),
        (20, 8,  '2025-12-28', '2025-12-30', 'Delivered',   54.99, 'CO', 'PayPal');
    SET IDENTITY_INSERT dbo.Orders OFF;
    PRINT '✅ Seeded Orders';
END
GO

-- Seed OrderItems
IF NOT EXISTS (SELECT 1 FROM dbo.OrderItems)
BEGIN
    SET IDENTITY_INSERT dbo.OrderItems ON;
    INSERT INTO dbo.OrderItems (OrderItemID, OrderID, ProductID, Quantity, UnitPrice, Discount) VALUES
        (1,  1,  1, 1, 1249.99, 0),  (2,  1,  3, 1,  179.99, 0),
        (3,  2,  6, 1,  129.99, 0),  (4,  2,  7, 2,   89.99, 10),
        (5,  3,  2, 1,  549.99, 0),  (6,  3,  10,4,   34.99, 0),
        (7,  4,  3, 1,  179.99, 0),
        (8,  5,  5, 1,  899.99, 0),
        (9,  6,  6, 1,  129.99, 0),  (10, 6,  7, 1,   89.99, 0),
        (11, 7,  8, 1,  349.99, 0),
        (12, 8,  10,2,   34.99, 0),  (13, 8,  12,3,   28.99, 0),
        (14, 9,  1, 1, 1249.99, 0),
        (15, 10, 2, 1,  549.99, 0),
        (16, 11, 4, 1,  299.99, 0),
        (17, 12, 7, 2,   89.99, 5),  (18, 12, 13,1,   54.99, 0),
        (19, 13, 1, 1, 1249.99, 15), (20, 13, 3,  1,  179.99, 0),
        (21, 14, 2, 1,  549.99, 10), (22, 14, 10, 4,   34.99, 0),
        (23, 15, 6, 1,  129.99, 0),
        (24, 16, 3, 1,  179.99, 0),
        (25, 17, 5, 1,  899.99, 0),  (26, 17, 3, 1,  179.99, 15),(27, 17, 13,1,  54.99, 0),
        (28, 18, 11,1,  119.99, 0),
        (29, 19, 8, 1,  349.99, 0),  (30, 19, 9,  2,   79.99, 0),
        (31, 20, 13,1,   54.99, 0);
    SET IDENTITY_INSERT dbo.OrderItems OFF;
    PRINT '✅ Seeded OrderItems';
END
GO

PRINT '✅ Section 1 complete: Operational tables ready';
GO

-- ============================================================
-- SECTION 2: Star Schema Tables (used by /api/analytics routes)
-- ============================================================

IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'CustomerDim' AND schema_id = SCHEMA_ID('dbo'))
BEGIN
    CREATE TABLE dbo.CustomerDim (
        CustomerID      INT PRIMARY KEY,
        CustomerName    NVARCHAR(200),
        Email           NVARCHAR(200),
        Region          NVARCHAR(50),
        CustomerSegment NVARCHAR(50),
        CreatedDate     DATETIME2
    );
    PRINT '✅ Created dbo.CustomerDim';
END
GO

IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'ProductDim' AND schema_id = SCHEMA_ID('dbo'))
BEGIN
    CREATE TABLE dbo.ProductDim (
        ProductID       INT PRIMARY KEY,
        ProductName     NVARCHAR(200),
        Category        NVARCHAR(100),
        SubCategory     NVARCHAR(100),
        UnitCost        DECIMAL(10,2),
        RetailPrice     DECIMAL(10,2),
        IsActive        BIT DEFAULT 1
    );
    PRINT '✅ Created dbo.ProductDim';
END
GO

IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'SalesFact' AND schema_id = SCHEMA_ID('dbo'))
BEGIN
    CREATE TABLE dbo.SalesFact (
        OrderID         INT PRIMARY KEY,
        CustomerID      INT,
        ProductID       INT,
        OrderDate       DATETIME2,
        Quantity        INT,
        UnitPrice       DECIMAL(10,2),
        TotalAmount     DECIMAL(10,2),
        Region          NVARCHAR(50)
    );
    PRINT '✅ Created dbo.SalesFact';
END
GO

TRUNCATE TABLE dbo.SalesFact;
DELETE FROM dbo.ProductDim;
DELETE FROM dbo.CustomerDim;

INSERT INTO dbo.CustomerDim (CustomerID, CustomerName, Email, Region, CustomerSegment, CreatedDate) VALUES
    (1,  'Alice Johnson',  'alice.johnson@email.com',  'West',      'Premium',  '2022-01-15'),
    (2,  'Bob Smith',      'bob.smith@email.com',       'South',     'Standard', '2022-03-20'),
    (3,  'Carol Williams', 'carol.williams@email.com',  'West',      'Premium',  '2022-06-10'),
    (4,  'David Brown',    'david.brown@email.com',     'East',      'Premium',  '2022-08-05'),
    (5,  'Eva Davis',      'eva.davis@email.com',       'South',     'Standard', '2022-09-18'),
    (6,  'Frank Miller',   'frank.miller@email.com',    'Midwest',   'Standard', '2022-11-02'),
    (7,  'Grace Wilson',   'grace.wilson@email.com',    'South',     'Premium',  '2023-01-14'),
    (8,  'Henry Moore',    'henry.moore@email.com',     'West',      'Standard', '2023-03-22'),
    (9,  'Iris Taylor',    'iris.taylor@email.com',     'West',      'Standard', '2023-05-30'),
    (10, 'Jack Anderson',  'jack.anderson@email.com',   'West',      'New',      '2023-07-11'),
    (11, 'Karen Thomas',   'karen.thomas@email.com',    'West',      'New',      '2023-08-19'),
    (12, 'Leo Jackson',    'leo.jackson@email.com',     'South',     'New',      '2023-09-25'),
    (13, 'Mia White',      'mia.white@email.com',       'West',      'New',      '2023-10-31'),
    (14, 'Nathan Harris',  'nathan.harris@email.com',   'East',      'New',      '2023-12-07'),
    (15, 'Olivia Martin',  'olivia.martin@email.com',   'South',     'New',      '2024-01-20');

INSERT INTO dbo.ProductDim (ProductID, ProductName, Category, SubCategory, UnitCost, RetailPrice) VALUES
    (1,  'ProBook Laptop 15"',       'Electronics', 'Computers',    850.00, 1249.99),
    (2,  'UltraTab Pro 11"',         'Electronics', 'Tablets',      310.00,  549.99),
    (3,  'AudioMax Headphones',      'Electronics', 'Audio',         80.00,  179.99),
    (4,  'SmartWatch Series 4',      'Electronics', 'Wearables',    150.00,  299.99),
    (5,  'CloudPhone X',             'Electronics', 'Phones',       520.00,  899.99),
    (6,  'AllWeather Jacket',        'Clothing',    'Outerwear',     55.00,  129.99),
    (7,  'TrailRunner Sneakers',     'Clothing',    'Footwear',      35.00,   89.99),
    (8,  'ErgoPro Desk Chair',       'Home',        'Office',       180.00,  349.99),
    (9,  'BrewMaster Coffee Maker',  'Home',        'Kitchen',       35.00,   79.99),
    (10, 'FitPro Yoga Mat',          'Sports',      'Fitness',       12.00,   34.99),
    (11, 'PowerLift Dumbbell Set',   'Sports',      'Weights',       55.00,  119.99),
    (12, 'The AI Era (Hardcover)',   'Books',       'Non-Fiction',    9.00,   28.99),
    (13, 'GlowSerum Daily Kit',      'Beauty',      'Skincare',      20.00,   54.99);

-- SalesFact rows spanning 2025-2026 (YEAR(GETDATE()) = 2026 queries hit these)
INSERT INTO dbo.SalesFact (OrderID, CustomerID, ProductID, OrderDate, Quantity, UnitPrice, TotalAmount, Region) VALUES
    (1,  1,  1, '2026-01-05', 1, 1249.99, 1429.98, 'West'),
    (2,  2,  6, '2026-01-12', 1,  129.99,  269.98, 'South'),
    (3,  3,  2, '2026-01-18', 1,  549.99,  729.98, 'West'),
    (4,  4,  3, '2026-01-25', 1,  179.99,  179.99, 'East'),
    (5,  5,  5, '2026-02-02', 1,  899.99,  899.99, 'South'),
    (6,  6,  6, '2026-02-09', 1,  129.99,  219.98, 'Midwest'),
    (7,  7,  8, '2026-02-14', 1,  349.99,  349.99, 'South'),
    (8,  8,  10,'2026-02-20', 2,   34.99,  154.98, 'West'),
    (9,  9,  1, '2026-02-27', 1, 1249.99, 1249.99, 'West'),
    (10, 10, 2, '2026-03-05', 1,  549.99,  549.99, 'West'),
    (11, 11, 4, '2026-03-08', 1,  299.99,  299.99, 'West'),
    (12, 12, 7, '2026-03-10', 2,   89.99,  209.98, 'South'),
    (13, 1,  1, '2025-10-14', 1, 1249.99,  849.98, 'West'),
    (14, 2,  2, '2025-10-22', 1,  549.99,  389.98, 'South'),
    (15, 3,  6, '2025-11-03', 1,  129.99,  129.99, 'West'),
    (16, 4,  3, '2025-11-15', 1,  179.99,  179.99, 'East'),
    (17, 5,  5, '2025-11-28', 1,  899.99,  954.97, 'South'),
    (18, 6,  11,'2025-12-05', 1,  119.99,  119.99, 'Midwest'),
    (19, 7,  8, '2025-12-19', 1,  349.99,  629.98, 'South'),
    (20, 8,  13,'2025-12-28', 1,   54.99,   54.99, 'West');

PRINT '✅ Section 2 complete: Star schema tables ready';
GO

-- ============================================================
-- SECTION 3: Gold Analytics Tables
-- (queried directly by agent_tools.py)
-- ============================================================

-- gold_sales_time_series
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'gold_sales_time_series' AND schema_id = SCHEMA_ID('dbo'))
BEGIN
    CREATE TABLE dbo.gold_sales_time_series (
        OrderDate           DATE,
        year                INT,
        quarter             INT,
        month               INT,
        month_name          NVARCHAR(20),
        daily_orders        BIGINT,
        daily_revenue       DECIMAL(22,2),
        avg_order_value     DECIMAL(16,6),
        unique_customers    BIGINT
    );
    PRINT '✅ Created dbo.gold_sales_time_series';
END
GO

TRUNCATE TABLE dbo.gold_sales_time_series;
INSERT INTO dbo.gold_sales_time_series
    (OrderDate,     year, quarter, month, month_name,    daily_orders, daily_revenue,  avg_order_value, unique_customers) VALUES
    ('2024-01-01',  2024, 1, 1,  'January',    420,  186540.00,  444.14, 318),
    ('2024-02-01',  2024, 1, 2,  'February',   398,  175810.00,  441.73, 304),
    ('2024-03-01',  2024, 1, 3,  'March',      467,  208990.00,  447.51, 352),
    ('2024-04-01',  2024, 2, 4,  'April',      511,  229640.00,  449.39, 386),
    ('2024-05-01',  2024, 2, 5,  'May',        548,  248560.00,  453.58, 412),
    ('2024-06-01',  2024, 2, 6,  'June',       532,  241450.00,  453.86, 401),
    ('2024-07-01',  2024, 3, 7,  'July',       575,  261700.00,  455.13, 435),
    ('2024-08-01',  2024, 3, 8,  'August',     601,  273830.00,  455.62, 452),
    ('2024-09-01',  2024, 3, 9,  'September',  588,  266920.00,  453.94, 443),
    ('2024-10-01',  2024, 4, 10, 'October',    624,  285990.00,  458.32, 470),
    ('2024-11-01',  2024, 4, 11, 'November',   798,  381560.00,  478.15, 598),  -- holiday spike
    ('2024-12-01',  2024, 4, 12, 'December',   912,  445890.00,  489.03, 681),  -- holiday spike
    ('2025-01-01',  2025, 1, 1,  'January',    445,  202680.00,  455.46, 338),
    ('2025-02-01',  2025, 1, 2,  'February',   422,  191230.00,  453.15, 321),
    ('2025-03-01',  2025, 1, 3,  'March',      498,  228440.00,  458.71, 376),
    ('2025-04-01',  2025, 2, 4,  'April',      541,  249770.00,  461.68, 409),
    ('2025-05-01',  2025, 2, 5,  'May',        579,  268590.00,  463.89, 436),
    ('2025-06-01',  2025, 2, 6,  'June',       563,  260480.00,  462.67, 424),
    ('2025-07-01',  2025, 3, 7,  'July',       607,  282210.00,  464.92, 458),
    ('2025-08-01',  2025, 3, 8,  'August',     638,  297350.00,  465.75, 480),
    ('2025-09-01',  2025, 3, 9,  'September',  621,  289180.00,  465.67, 468),
    ('2025-10-01',  2025, 4, 10, 'October',    659,  309840.00,  470.17, 496),
    ('2025-11-01',  2025, 4, 11, 'November',   842,  412640.00,  489.95, 631),  -- holiday spike
    ('2025-12-01',  2025, 4, 12, 'December',   967,  484250.00,  500.78, 723),  -- holiday spike
    ('2026-01-01',  2026, 1, 1,  'January',    471,  220340.00,  467.81, 357),
    ('2026-02-01',  2026, 1, 2,  'February',   448,  207620.00,  463.44, 340),
    ('2026-03-01',  2026, 1, 3,  'March',      520,  244190.00,  469.60, 392);  -- current month (partial)

PRINT '✅ Seeded gold_sales_time_series (27 months: Jan 2024 – Mar 2026)';
GO

-- gold_geographic_sales
-- NOTE: includes year/quarter/month so agent_tools.py time-filters work correctly
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'gold_geographic_sales' AND schema_id = SCHEMA_ID('dbo'))
BEGIN
    CREATE TABLE dbo.gold_geographic_sales (
        State               NVARCHAR(50),
        City                NVARCHAR(100),
        year                INT,
        quarter             INT,
        month               INT,
        total_orders        BIGINT,
        total_revenue       DECIMAL(22,2),
        unique_customers    BIGINT,
        avg_order_value     DECIMAL(16,6),
        state_rank          INT
    );
    PRINT '✅ Created dbo.gold_geographic_sales';
END
GO

TRUNCATE TABLE dbo.gold_geographic_sales;
INSERT INTO dbo.gold_geographic_sales
    (State, City,           year, quarter, month, total_orders, total_revenue, unique_customers, avg_order_value, state_rank) VALUES
    -- 2026 Q1 (current)
    ('CA', 'Los Angeles',   2026, 1, 1, 142, 68540.00, 108, 482.68, 1),
    ('TX', 'Houston',       2026, 1, 1, 118, 53220.00,  90, 451.02, 2),
    ('WA', 'Seattle',       2026, 1, 1,  96, 42890.00,  73, 446.77, 3),
    ('NY', 'New York',      2026, 1, 1,  88, 39340.00,  67, 447.05, 4),
    ('FL', 'Miami',         2026, 1, 1,  79, 35120.00,  61, 444.56, 5),
    ('IL', 'Chicago',       2026, 1, 1,  67, 29640.00,  52, 442.39, 6),
    ('GA', 'Atlanta',       2026, 1, 1,  61, 26890.00,  47, 440.82, 7),
    ('CO', 'Denver',        2026, 1, 1,  54, 23680.00,  41, 438.52, 8),
    ('AZ', 'Phoenix',       2026, 1, 1,  48, 20940.00,  36, 436.25, 9),
    ('OR', 'Portland',      2026, 1, 1,  43, 18560.00,  32, 431.63, 10),
    -- 2026 Q1 month 2
    ('CA', 'Los Angeles',   2026, 1, 2, 138, 65820.00, 105, 476.96, 1),
    ('TX', 'Houston',       2026, 1, 2, 114, 50940.00,  87, 446.84, 2),
    ('WA', 'Seattle',       2026, 1, 2,  93, 41100.00,  70, 441.94, 3),
    ('NY', 'New York',      2026, 1, 2,  85, 37620.00,  65, 442.59, 4),
    ('FL', 'Miami',         2026, 1, 2,  76, 33540.00,  58, 441.32, 5),
    -- 2026 Q1 month 3
    ('CA', 'Los Angeles',   2026, 1, 3, 150, 73200.00, 114, 488.00, 1),
    ('TX', 'Houston',       2026, 1, 3, 122, 56340.00,  93, 461.80, 2),
    ('WA', 'Seattle',       2026, 1, 3, 100, 45610.00,  76, 456.10, 3),
    -- 2025 full year summary rows
    ('CA', 'Los Angeles',   2025, 4, 12, 980, 489200.00, 740, 499.18, 1),
    ('TX', 'Houston',       2025, 4, 12, 810, 393840.00, 612, 486.22, 2),
    ('WA', 'Seattle',       2025, 4, 12, 658, 312540.00, 498, 474.98, 3),
    ('NY', 'New York',      2025, 4, 12, 602, 283740.00, 454, 471.33, 4),
    ('FL', 'Miami',         2025, 4, 12, 541, 252890.00, 409, 467.45, 5);

PRINT '✅ Seeded gold_geographic_sales';
GO

-- gold_customer_360
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'gold_customer_360' AND schema_id = SCHEMA_ID('dbo'))
BEGIN
    CREATE TABLE dbo.gold_customer_360 (
        CustomerID              INT,
        FirstName               NVARCHAR(100),
        LastName                NVARCHAR(100),
        Email                   NVARCHAR(255),
        City                    NVARCHAR(100),
        State                   NVARCHAR(50),
        Country                 NVARCHAR(100),
        CustomerSince           DATETIME2,
        total_orders            BIGINT,
        lifetime_value          DECIMAL(22,2),
        avg_order_value         DECIMAL(16,6),
        last_order_date         DATE,
        first_order_date        DATE,
        avg_delivery_days       FLOAT,
        customer_tenure_days    INT,
        recency_days            INT,
        customer_segment        NVARCHAR(50),
        customer_status         NVARCHAR(50)
    );
    PRINT '✅ Created dbo.gold_customer_360';
END
GO

TRUNCATE TABLE dbo.gold_customer_360;
INSERT INTO dbo.gold_customer_360 VALUES
    (1,  'Alice',  'Johnson',  'alice.johnson@email.com',  'Los Angeles', 'CA', 'USA', '2022-01-15', 12, 8940.75, 745.06, '2026-01-05', '2022-02-10', 2.1, 1522, 71,  'Premium',  'Active'),
    (2,  'Bob',    'Smith',    'bob.smith@email.com',      'Houston',     'TX', 'USA', '2022-03-20',  9, 5820.40, 646.71, '2026-01-12', '2022-04-15', 2.4, 1458, 64,  'Standard', 'Active'),
    (3,  'Carol',  'Williams', 'carol.williams@email.com', 'Seattle',     'WA', 'USA', '2022-06-10',  8, 5240.30, 655.04, '2026-01-18', '2022-07-01', 1.9, 1377, 58,  'Premium',  'Active'),
    (4,  'David',  'Brown',    'david.brown@email.com',    'New York',    'NY', 'USA', '2022-08-05',  7, 4380.65, 625.81, '2026-01-25', '2022-09-12', 2.2, 1320, 51,  'Premium',  'Active'),
    (5,  'Eva',    'Davis',    'eva.davis@email.com',      'Miami',       'FL', 'USA', '2022-09-18',  6, 3920.48, 653.41, '2026-02-02', '2022-10-20', 2.0, 1276, 43,  'Standard', 'Active'),
    (6,  'Frank',  'Miller',   'frank.miller@email.com',   'Chicago',     'IL', 'USA', '2022-11-02',  5, 2840.22, 568.04, '2026-02-09', '2022-12-10', 2.8, 1231, 36,  'Standard', 'Active'),
    (7,  'Grace',  'Wilson',   'grace.wilson@email.com',   'Atlanta',     'GA', 'USA', '2023-01-14',  5, 3610.15, 722.03, '2026-02-14', '2023-02-20', 1.8, 1158, 31,  'Premium',  'Active'),
    (8,  'Henry',  'Moore',    'henry.moore@email.com',    'Denver',      'CO', 'USA', '2023-03-22',  4, 1980.88, 495.22, '2026-02-20', '2023-04-15', 2.6, 1091, 25,  'Standard', 'Active'),
    (9,  'Iris',   'Taylor',   'iris.taylor@email.com',    'Phoenix',     'AZ', 'USA', '2023-05-30',  3, 2340.45, 780.15, '2026-02-27', '2023-06-18', 2.3, 1022, 18,  'Standard', 'Active'),
    (10, 'Jack',   'Anderson', 'jack.anderson@email.com',  'Portland',    'OR', 'USA', '2023-07-11',  2,  980.60, 490.30, '2026-03-05', '2023-08-01', 3.1,  980, 12,  'New',      'Active'),
    (11, 'Karen',  'Thomas',   'karen.thomas@email.com',   'San Diego',   'CA', 'USA', '2023-08-19',  2,  620.40, 310.20, '2026-03-08', '2023-09-10', 2.7,  941,  9,  'New',      'Active'),
    (12, 'Leo',    'Jackson',  'leo.jackson@email.com',    'Austin',      'TX', 'USA', '2023-09-25',  2,  440.20, 220.10, '2026-03-10', '2023-10-15', 3.0,  904,  7,  'New',      'Active'),
    (13, 'Mia',    'White',    'mia.white@email.com',      'Bellevue',    'WA', 'USA', '2023-10-31',  1,  360.99, 360.99, '2025-11-01', '2023-11-20', 2.5,  868, 136, 'New',      'At Risk'),
    (14, 'Nathan', 'Harris',   'nathan.harris@email.com',  'Brooklyn',    'NY', 'USA', '2023-12-07',  1,  199.99, 199.99, '2024-01-10', '2024-01-10', 4.2,  831, 431, 'New',      'Churned'),
    (15, 'Olivia', 'Martin',   'olivia.martin@email.com',  'Orlando',     'FL', 'USA', '2024-01-20',  1,  449.99, 449.99, '2024-04-01', '2024-04-01', 3.8,  787, 350, 'New',      'Inactive');

PRINT '✅ Seeded gold_customer_360';
GO

-- gold_inventory_analysis
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'gold_inventory_analysis' AND schema_id = SCHEMA_ID('dbo'))
BEGIN
    CREATE TABLE dbo.gold_inventory_analysis (
        ProductID               INT,
        ProductName             NVARCHAR(200),
        CategoryName            NVARCHAR(100),
        SKU                     NVARCHAR(50),
        StockQuantity           INT,
        total_sold              BIGINT,
        order_frequency         BIGINT,
        stock_to_sales_ratio    FLOAT,
        stock_status            NVARCHAR(50),
        reorder_priority        INT
    );
    PRINT '✅ Created dbo.gold_inventory_analysis';
END
GO

TRUNCATE TABLE dbo.gold_inventory_analysis;
INSERT INTO dbo.gold_inventory_analysis VALUES
    (1,  'ProBook Laptop 15"',       'Electronics', 'ELEC-LP-001',  85,  342, 280, 0.25, 'Low Stock',    1),
    (2,  'UltraTab Pro 11"',         'Electronics', 'ELEC-TB-001', 120,  289, 240, 0.41, 'In Stock',     2),
    (3,  'AudioMax Headphones',      'Electronics', 'ELEC-HP-001', 200,  521, 430, 0.38, 'In Stock',     4),
    (4,  'SmartWatch Series 4',      'Electronics', 'ELEC-SW-001', 150,  310, 260, 0.48, 'In Stock',     3),
    (5,  'CloudPhone X',             'Electronics', 'ELEC-PH-001',  95,  198, 165, 0.48, 'In Stock',     5),
    (6,  'AllWeather Jacket',        'Clothing',    'CLTH-JK-001', 310,  640, 530, 0.48, 'In Stock',     6),
    (7,  'TrailRunner Sneakers',     'Clothing',    'CLTH-SN-001', 420,  820, 681, 0.51, 'In Stock',     7),
    (8,  'ErgoPro Desk Chair',       'Home',        'HOME-CH-001',  60,  180, 150, 0.33, 'Low Stock',    2),
    (9,  'BrewMaster Coffee Maker',  'Home',        'HOME-CM-001', 180,  410, 340, 0.44, 'In Stock',     8),
    (10, 'FitPro Yoga Mat',          'Sports',      'SPRT-YM-001', 500, 1240, 980, 0.40, 'In Stock',     9),
    (11, 'PowerLift Dumbbell Set',   'Sports',      'SPRT-DB-001',  75,  190, 158, 0.39, 'Low Stock',    3),
    (12, 'The AI Era (Hardcover)',   'Books',       'BOOK-AI-001', 600,  980, 840, 0.61, 'In Stock',    10),
    (13, 'GlowSerum Daily Kit',      'Beauty',      'BEAU-SK-001', 250,  520, 430, 0.48, 'In Stock',    11),
    (1,  'ProBook Laptop 15"',       'Electronics', 'ELEC-LP-001',   0,   12,  10, 0.00, 'Out of Stock', 1);  -- warehouse B

PRINT '✅ Seeded gold_inventory_analysis';
GO

-- gold_sales_performance
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'gold_sales_performance' AND schema_id = SCHEMA_ID('dbo'))
BEGIN
    CREATE TABLE dbo.gold_sales_performance (
        metric              NVARCHAR(100),
        actual_value        FLOAT,
        target_value        FLOAT,
        achievement_pct     FLOAT,
        variance            FLOAT,
        period              NVARCHAR(50),
        status              NVARCHAR(50)
    );
    PRINT '✅ Created dbo.gold_sales_performance';
END
GO

TRUNCATE TABLE dbo.gold_sales_performance;
INSERT INTO dbo.gold_sales_performance VALUES
    ('Total Revenue',        471950.00, 450000.00, 104.88,  21950.00, 'Q1 2026', 'Above Target'),
    ('Conversion Rate',           3.84,      4.00,  96.00,     -0.16, 'Q1 2026', 'Below Target'),
    ('Average Deal Size',       469.25,    460.00, 101.90,      9.25, 'Q1 2026', 'Above Target'),
    ('Win Rate',                  62.40,     65.00,  96.00,     -2.60, 'Q1 2026', 'Below Target'),
    ('Customer Acquisition',     389.00,    400.00,  97.25,    -11.00, 'Q1 2026', 'Below Target'),
    ('Repeat Purchase Rate',      41.20,     38.00, 108.42,      3.20, 'Q1 2026', 'Above Target');

PRINT '✅ Seeded gold_sales_performance';
GO

-- gold_shipping_performance
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'gold_shipping_performance' AND schema_id = SCHEMA_ID('dbo'))
BEGIN
    CREATE TABLE dbo.gold_shipping_performance (
        ShippingState       NVARCHAR(50),
        shipment_count      BIGINT,
        avg_days_to_ship    FLOAT,
        min_days_to_ship    INT,
        max_days_to_ship    INT,
        median_days_to_ship INT,
        p95_days_to_ship    INT,
        performance_rating  NVARCHAR(50)
    );
    PRINT '✅ Created dbo.gold_shipping_performance';
END
GO

TRUNCATE TABLE dbo.gold_shipping_performance;
INSERT INTO dbo.gold_shipping_performance VALUES
    ('CA', 1840, 1.8, 1, 5,  2, 4, 'Excellent'),
    ('TX', 1520, 2.1, 1, 6,  2, 5, 'Good'),
    ('WA', 1240, 1.9, 1, 5,  2, 4, 'Excellent'),
    ('NY', 1130, 2.4, 1, 7,  2, 5, 'Good'),
    ('FL', 1010, 2.3, 1, 6,  2, 5, 'Good'),
    ('IL',  860, 2.6, 1, 7,  3, 6, 'Acceptable'),
    ('GA',  780, 2.8, 1, 8,  3, 6, 'Acceptable'),
    ('CO',  690, 3.1, 1, 8,  3, 7, 'Needs Improvement'),
    ('AZ',  610, 3.0, 1, 7,  3, 6, 'Acceptable'),
    ('OR',  540, 2.5, 1, 6,  2, 5, 'Good');

PRINT '✅ Seeded gold_shipping_performance';
GO

-- gold_support_metrics
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'gold_support_metrics' AND schema_id = SCHEMA_ID('dbo'))
BEGIN
    CREATE TABLE dbo.gold_support_metrics (
        CustomerID              INT,
        total_tickets           BIGINT,
        open_tickets            BIGINT,
        critical_tickets        BIGINT,
        avg_resolution_time     FLOAT,
        support_health          NVARCHAR(50),
        FirstName               NVARCHAR(100),
        LastName                NVARCHAR(100),
        Email                   NVARCHAR(255)
    );
    PRINT '✅ Created dbo.gold_support_metrics';
END
GO

TRUNCATE TABLE dbo.gold_support_metrics;
INSERT INTO dbo.gold_support_metrics VALUES
    (1,  4, 0, 0,  18.5, 'Healthy',  'Alice',  'Johnson',  'alice.johnson@email.com'),
    (2,  6, 1, 0,  24.2, 'Watch',    'Bob',    'Smith',    'bob.smith@email.com'),
    (3,  2, 0, 0,  15.8, 'Healthy',  'Carol',  'Williams', 'carol.williams@email.com'),
    (4,  8, 2, 1,  42.6, 'Critical', 'David',  'Brown',    'david.brown@email.com'),
    (5,  3, 0, 0,  20.1, 'Healthy',  'Eva',    'Davis',    'eva.davis@email.com'),
    (6,  1, 1, 0,  12.0, 'Watch',    'Frank',  'Miller',   'frank.miller@email.com'),
    (7,  5, 0, 0,  19.4, 'Healthy',  'Grace',  'Wilson',   'grace.wilson@email.com'),
    (8,  2, 0, 0,  22.3, 'Healthy',  'Henry',  'Moore',    'henry.moore@email.com'),
    (9,  1, 0, 0,  16.7, 'Healthy',  'Iris',   'Taylor',   'iris.taylor@email.com'),
    (10, 0, 0, 0,   0.0, 'Healthy',  'Jack',   'Anderson', 'jack.anderson@email.com');

PRINT '✅ Seeded gold_support_metrics';
GO

-- gold_cohort_analysis
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'gold_cohort_analysis' AND schema_id = SCHEMA_ID('dbo'))
BEGIN
    CREATE TABLE dbo.gold_cohort_analysis (
        cohort_month                NVARCHAR(20),
        months_since_first_order    INT,
        active_customers            BIGINT,
        cohort_revenue              DECIMAL(22,2),
        cohort_orders               BIGINT,
        cohort_size                 BIGINT,
        retention_rate              DECIMAL(5,2)
    );
    PRINT '✅ Created dbo.gold_cohort_analysis';
END
GO

TRUNCATE TABLE dbo.gold_cohort_analysis;
INSERT INTO dbo.gold_cohort_analysis VALUES
    ('2025-04', 1,  312, 148560.00,  408, 390, 80.00),
    ('2025-05', 1,  328, 159840.00,  430, 410, 80.00),
    ('2025-06', 1,  298, 138920.00,  385, 375, 79.47),
    ('2025-07', 1,  341, 165340.00,  452, 425, 80.24),
    ('2025-08', 1,  358, 174960.00,  474, 445, 80.45),
    ('2025-09', 1,  335, 161820.00,  441, 420, 79.76),
    ('2025-10', 1,  372, 182440.00,  496, 464, 80.17),
    ('2025-11', 1,  480, 248560.00,  640, 598, 80.27),  -- holiday cohort
    ('2025-12', 1,  528, 279840.00,  702, 658, 80.24),  -- holiday cohort
    ('2026-01', 1,  285, 133420.00,  357, 357, 79.83),
    ('2026-02', 1,  272, 125330.00,  340, 340, 80.00),
    ('2026-03', 1,  240, 112680.00,  300, 300, 80.00);  -- current month (partial)

PRINT '✅ Seeded gold_cohort_analysis';
GO

-- ============================================================
-- SECTION 4: Point agent_tools.py at this DB
-- Set FABRIC_CONNECTION_STRING = same as DATABASE_URL in App Settings,
-- OR deploy with the env var below (no separate Fabric workspace needed):
--
--   FABRIC_CONNECTION_STRING =
--     DRIVER={ODBC Driver 18 for SQL Server};
--     SERVER=<your-server>.database.windows.net;
--     DATABASE=aiagentsdb;
--     Authentication=ActiveDirectoryMsi;
--     Encrypt=yes
--
-- ============================================================

-- gold_upsell_opportunities
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'gold_upsell_opportunities' AND schema_id = SCHEMA_ID('dbo'))
BEGIN
    CREATE TABLE dbo.gold_upsell_opportunities (
        OpportunityID       INT IDENTITY(1,1) PRIMARY KEY,
        CustomerID          INT NOT NULL,
        recommended_action  NVARCHAR(200) NOT NULL,
        upsell_score        DECIMAL(4,2) NOT NULL
    );
    PRINT '✅ Created dbo.gold_upsell_opportunities';
END
GO

TRUNCATE TABLE dbo.gold_upsell_opportunities;
INSERT INTO dbo.gold_upsell_opportunities (CustomerID, recommended_action, upsell_score) VALUES
    (1,  'Premium Upgrade',         0.92),
    (2,  'Enterprise License',      0.85),
    (3,  'AI Analytics Module',     0.78),
    (4,  'Add Support Plan',        0.72),
    (5,  'Cloud Storage Expansion', 0.88),
    (6,  'Training Package',        0.65),
    (7,  'Integration Suite',       0.55),
    (8,  'Premium Upgrade',         0.45),
    (9,  'AI Analytics Module',     0.82),
    (10, 'Enterprise License',      0.38),
    (11, 'Add Support Plan',        0.91),
    (12, 'Cloud Storage Expansion', 0.62),
    (13, 'Training Package',        0.35),
    (1,  'Integration Suite',       0.70),
    (2,  'AI Analytics Module',     0.58);

PRINT '✅ Seeded gold_upsell_opportunities';
GO

PRINT '';
PRINT '============================================================';
PRINT '✅ All synthetic data loaded successfully!';
PRINT '============================================================';
PRINT '';
PRINT 'Tables created and seeded:';
PRINT '  Operational : Categories, Products, Customers, Orders, OrderItems';
PRINT '  Star schema : CustomerDim, ProductDim, SalesFact';
PRINT '  Gold tables : gold_sales_time_series (27 months)';
PRINT '                gold_geographic_sales';
PRINT '                gold_customer_360';
PRINT '                gold_inventory_analysis';
PRINT '                gold_sales_performance';
PRINT '                gold_shipping_performance';
PRINT '                gold_support_metrics';
PRINT '                gold_cohort_analysis';
PRINT '                gold_upsell_opportunities';
PRINT '';
PRINT 'Next step: set FABRIC_CONNECTION_STRING in App Service';
PRINT 'to the same connection string as your main SQL database.';
GO
