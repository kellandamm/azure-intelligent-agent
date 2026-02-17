-- ========================================
-- Azure SQL Database Schema Setup
-- Database: <your-sql-server>.database.windows.net
-- ========================================

-- Drop existing tables if they exist (in reverse order due to foreign keys)
IF OBJECT_ID('dbo.OrderItems', 'U') IS NOT NULL DROP TABLE dbo.OrderItems;
IF OBJECT_ID('dbo.Orders', 'U') IS NOT NULL DROP TABLE dbo.Orders;
IF OBJECT_ID('dbo.Customers', 'U') IS NOT NULL DROP TABLE dbo.Customers;
IF OBJECT_ID('dbo.Products', 'U') IS NOT NULL DROP TABLE dbo.Products;
IF OBJECT_ID('dbo.Categories', 'U') IS NOT NULL DROP TABLE dbo.Categories;
GO

-- ========================================
-- Categories Table
-- ========================================
CREATE TABLE dbo.Categories (
    CategoryID INT IDENTITY(1,1) PRIMARY KEY,
    CategoryName NVARCHAR(100) NOT NULL,
    Description NVARCHAR(500),
    CreatedDate DATETIME2 DEFAULT GETUTCDATE(),
    ModifiedDate DATETIME2 DEFAULT GETUTCDATE()
);
GO

CREATE INDEX IX_Categories_CategoryName ON dbo.Categories(CategoryName);
GO

-- ========================================
-- Products Table
-- ========================================
CREATE TABLE dbo.Products (
    ProductID INT IDENTITY(1,1) PRIMARY KEY,
    ProductName NVARCHAR(200) NOT NULL,
    CategoryID INT NOT NULL,
    Price DECIMAL(10,2) NOT NULL CHECK (Price >= 0),
    StockQuantity INT NOT NULL DEFAULT 0 CHECK (StockQuantity >= 0),
    Description NVARCHAR(1000),
    SKU NVARCHAR(50) UNIQUE,
    IsActive BIT DEFAULT 1,
    CreatedDate DATETIME2 DEFAULT GETUTCDATE(),
    ModifiedDate DATETIME2 DEFAULT GETUTCDATE(),
    CONSTRAINT FK_Products_Categories FOREIGN KEY (CategoryID) 
        REFERENCES dbo.Categories(CategoryID)
);
GO

CREATE INDEX IX_Products_CategoryID ON dbo.Products(CategoryID);
CREATE INDEX IX_Products_ProductName ON dbo.Products(ProductName);
CREATE INDEX IX_Products_SKU ON dbo.Products(SKU);
GO

-- ========================================
-- Customers Table
-- ========================================
CREATE TABLE dbo.Customers (
    CustomerID INT IDENTITY(1,1) PRIMARY KEY,
    FirstName NVARCHAR(100) NOT NULL,
    LastName NVARCHAR(100) NOT NULL,
    Email NVARCHAR(255) NOT NULL UNIQUE,
    PhoneNumber NVARCHAR(20),
    Address NVARCHAR(500),
    City NVARCHAR(100),
    State NVARCHAR(50),
    ZipCode NVARCHAR(20),
    Country NVARCHAR(100) DEFAULT 'USA',
    CustomerSince DATETIME2 DEFAULT GETUTCDATE(),
    IsActive BIT DEFAULT 1,
    CreatedDate DATETIME2 DEFAULT GETUTCDATE(),
    ModifiedDate DATETIME2 DEFAULT GETUTCDATE()
);
GO

CREATE INDEX IX_Customers_Email ON dbo.Customers(Email);
CREATE INDEX IX_Customers_LastName ON dbo.Customers(LastName, FirstName);
CREATE INDEX IX_Customers_City ON dbo.Customers(City);
GO

-- ========================================
-- Orders Table
-- ========================================
CREATE TABLE dbo.Orders (
    OrderID INT IDENTITY(1,1) PRIMARY KEY,
    CustomerID INT NOT NULL,
    OrderDate DATETIME2 DEFAULT GETUTCDATE(),
    ShippedDate DATETIME2,
    OrderStatus NVARCHAR(50) NOT NULL DEFAULT 'Pending' 
        CHECK (OrderStatus IN ('Pending', 'Processing', 'Shipped', 'Delivered', 'Cancelled')),
    TotalAmount DECIMAL(12,2) NOT NULL DEFAULT 0 CHECK (TotalAmount >= 0),
    ShippingAddress NVARCHAR(500),
    ShippingCity NVARCHAR(100),
    ShippingState NVARCHAR(50),
    ShippingZipCode NVARCHAR(20),
    ShippingCountry NVARCHAR(100) DEFAULT 'USA',
    PaymentMethod NVARCHAR(50),
    CreatedDate DATETIME2 DEFAULT GETUTCDATE(),
    ModifiedDate DATETIME2 DEFAULT GETUTCDATE(),
    CONSTRAINT FK_Orders_Customers FOREIGN KEY (CustomerID) 
        REFERENCES dbo.Customers(CustomerID)
);
GO

CREATE INDEX IX_Orders_CustomerID ON dbo.Orders(CustomerID);
CREATE INDEX IX_Orders_OrderDate ON dbo.Orders(OrderDate);
CREATE INDEX IX_Orders_OrderStatus ON dbo.Orders(OrderStatus);
GO

-- ========================================
-- OrderItems Table
-- ========================================
CREATE TABLE dbo.OrderItems (
    OrderItemID INT IDENTITY(1,1) PRIMARY KEY,
    OrderID INT NOT NULL,
    ProductID INT NOT NULL,
    Quantity INT NOT NULL CHECK (Quantity > 0),
    UnitPrice DECIMAL(10,2) NOT NULL CHECK (UnitPrice >= 0),
    Discount DECIMAL(5,2) DEFAULT 0 CHECK (Discount >= 0 AND Discount <= 100),
    LineTotal AS (Quantity * UnitPrice * (1 - Discount/100)) PERSISTED,
    CreatedDate DATETIME2 DEFAULT GETUTCDATE(),
    ModifiedDate DATETIME2 DEFAULT GETUTCDATE(),
    CONSTRAINT FK_OrderItems_Orders FOREIGN KEY (OrderID) 
        REFERENCES dbo.Orders(OrderID) ON DELETE CASCADE,
    CONSTRAINT FK_OrderItems_Products FOREIGN KEY (ProductID) 
        REFERENCES dbo.Products(ProductID)
);
GO

CREATE INDEX IX_OrderItems_OrderID ON dbo.OrderItems(OrderID);
CREATE INDEX IX_OrderItems_ProductID ON dbo.OrderItems(ProductID);
GO

-- ========================================
-- Insert Initial Seed Data
-- ========================================

-- Seed Categories
SET IDENTITY_INSERT dbo.Categories ON;
INSERT INTO dbo.Categories (CategoryID, CategoryName, Description) VALUES
(1, 'Electronics', 'Electronic devices and accessories'),
(2, 'Clothing', 'Apparel and fashion items'),
(3, 'Home & Garden', 'Home improvement and garden supplies'),
(4, 'Sports & Outdoors', 'Sports equipment and outdoor gear'),
(5, 'Books', 'Books and educational materials'),
(6, 'Toys & Games', 'Toys, games, and entertainment'),
(7, 'Health & Beauty', 'Health, beauty, and personal care products'),
(8, 'Food & Beverage', 'Food, drinks, and gourmet items'),
(9, 'Automotive', 'Auto parts and accessories'),
(10, 'Office Supplies', 'Office and school supplies');
SET IDENTITY_INSERT dbo.Categories OFF;
GO

PRINT 'Schema created successfully!';
PRINT 'Categories seeded with 10 initial records.';
PRINT 'Ready for synthetic data generation.';
GO
