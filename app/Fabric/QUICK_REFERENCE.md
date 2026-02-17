# 🎯 Quick Reference - Synthetic Data Generator

## 📁 Project Structure

```
<your-repo-path>/app/Fabric/
├── schema.sql                      # Database schema with all tables
├── generate_initial_data.py        # One-time script to create initial data
├── function_app.py                 # Azure Function (runs every 24 hours)
├── requirements.txt                # Python dependencies
├── host.json                       # Azure Functions configuration
├── local.settings.json.template    # Configuration template
├── .funcignore                     # Files to exclude from deployment
├── .gitignore                      # Git ignore rules
├── quick-start.ps1                 # Interactive setup script
├── deploy-to-azure.ps1            # Automated deployment script
├── README.md                       # Complete documentation
└── DATABASE_SETUP.md              # Database configuration guide
```

## 🗄️ Database Tables

| Table | Purpose | Initial Records | Daily Generated |
|-------|---------|-----------------|-----------------|
| Categories | Product categories | 10 (pre-seeded) | 0 |
| Products | Product catalog | 100 | 50 |
| Customers | Customer data | 200 | 100 |
| Orders | Customer orders | 300 | 200 |
| OrderItems | Order line items | 600+ | 400-600 |

**Total Initial:** ~1,210 records  
**Total Daily:** ~500-550 new records  
**Monthly Growth:** ~15,000 records

## ⚡ Quick Start Commands

### 1️⃣ Setup Database

```sql
-- Connect to Azure SQL and run:
sqlcmd -S <your-sql-server>.database.windows.net -d YourDB -U YourUser -i schema.sql
```

### 2️⃣ Configure Local Settings

```powershell
# Copy template
cp local.settings.json.template local.settings.json

# Edit with your credentials
code local.settings.json
```

### 3️⃣ Generate Initial Data

```powershell
# Set environment variables
$env:SQL_DATABASE="YourDatabaseName"
$env:SQL_USERNAME="YourUsername"
$env:SQL_PASSWORD="YourPassword"

# Run script
python generate_initial_data.py
```

### 4️⃣ Test Locally

```powershell
# Install dependencies
pip install -r requirements.txt

# Start function locally
func start
```

### 5️⃣ Deploy to Azure

```powershell
.\deploy-to-azure.ps1 `
  -SqlDatabase "YourDB" `
  -SqlUsername "YourUser" `
  -SqlPassword "YourPass"
```

## 🔧 Configuration

### Environment Variables

```json
{
  "SQL_SERVER": "<your-sql-server>.database.windows.net",
  "SQL_DATABASE": "your_database_name",
  "SQL_USERNAME": "your_username",
  "SQL_PASSWORD": "your_password"
}
```

### Timer Schedule

Current: `0 0 0 * * *` (Daily at midnight UTC)

Common alternatives:
- Every hour: `0 0 * * * *`
- Every 6 hours: `0 0 */6 * * *`
- Every Monday: `0 0 0 * * 1`

## 📊 Data Distribution (per 500 records)

```
Products (50)
├── Electronics (5)
├── Clothing (5)
├── Home & Garden (5)
├── Sports & Outdoors (5)
├── Books (5)
├── Toys & Games (5)
├── Health & Beauty (5)
├── Food & Beverage (5)
├── Automotive (5)
└── Office Supplies (5)

Customers (100)
├── Random names (Faker)
├── Unique emails
├── US addresses
└── Phone numbers

Orders (200)
├── Order Status:
│   ├── Pending (40%)
│   ├── Processing (20%)
│   ├── Shipped (20%)
│   ├── Delivered (15%)
│   └── Cancelled (5%)
└── Payment Methods:
    ├── Credit Card
    ├── Debit Card
    ├── PayPal
    ├── Apple Pay
    ├── Google Pay
    └── Bank Transfer

OrderItems (400-600)
├── 2-3 items per order
├── Quantity: 1-5
├── Discounts: 0-20%
└── Prices from Products table
```

## 🔍 Useful SQL Queries

### Check Record Counts

```sql
SELECT 
    'Categories' AS TableName, COUNT(*) AS RecordCount FROM dbo.Categories
UNION ALL
SELECT 'Products', COUNT(*) FROM dbo.Products
UNION ALL
SELECT 'Customers', COUNT(*) FROM dbo.Customers
UNION ALL
SELECT 'Orders', COUNT(*) FROM dbo.Orders
UNION ALL
SELECT 'OrderItems', COUNT(*) FROM dbo.OrderItems;
```

### Recent Orders

```sql
SELECT TOP 10
    o.OrderID,
    c.FirstName + ' ' + c.LastName AS CustomerName,
    o.OrderDate,
    o.OrderStatus,
    o.TotalAmount
FROM dbo.Orders o
JOIN dbo.Customers c ON o.CustomerID = c.CustomerID
ORDER BY o.OrderDate DESC;
```

### Sales by Category

```sql
SELECT 
    cat.CategoryName,
    COUNT(DISTINCT o.OrderID) AS OrderCount,
    SUM(oi.Quantity) AS TotalQuantity,
    SUM(oi.LineTotal) AS TotalRevenue
FROM dbo.Categories cat
JOIN dbo.Products p ON cat.CategoryID = p.CategoryID
JOIN dbo.OrderItems oi ON p.ProductID = oi.ProductID
JOIN dbo.Orders o ON oi.OrderID = o.OrderID
GROUP BY cat.CategoryName
ORDER BY TotalRevenue DESC;
```

### Top Customers

```sql
SELECT TOP 10
    c.CustomerID,
    c.FirstName + ' ' + c.LastName AS CustomerName,
    COUNT(o.OrderID) AS OrderCount,
    SUM(o.TotalAmount) AS TotalSpent
FROM dbo.Customers c
JOIN dbo.Orders o ON c.CustomerID = o.CustomerID
GROUP BY c.CustomerID, c.FirstName, c.LastName
ORDER BY TotalSpent DESC;
```

## 📈 Monitoring

### View Function Logs (Azure)

```powershell
# Real-time logs
az functionapp logs tail --name YourFunctionApp --resource-group YourResourceGroup

# Specific time range
az monitor activity-log list --resource-group YourResourceGroup --start-time 2024-01-01 --end-time 2024-01-02
```

### Check Last Execution

```sql
SELECT 
    MAX(CreatedDate) AS LastProductCreated,
    (SELECT MAX(CreatedDate) FROM dbo.Customers) AS LastCustomerCreated,
    (SELECT MAX(CreatedDate) FROM dbo.Orders) AS LastOrderCreated
FROM dbo.Products;
```

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| ODBC Driver not found | Install ODBC Driver 18 for SQL Server |
| Login failed | Check credentials and firewall rules |
| Function not triggering | Verify schedule syntax and app settings |
| Duplicate key errors | Normal - function handles gracefully |
| Slow performance | Check database DTU/vCore usage |

## 🔒 Security Checklist

- [ ] Store passwords in Azure Key Vault
- [ ] Use managed identity for Azure Function
- [ ] Configure SQL firewall rules
- [ ] Enable VNet integration (production)
- [ ] Use Azure AD authentication
- [ ] Enable audit logging
- [ ] Set up alerts for suspicious activity

## 📞 Support Resources

- **Documentation:** `README.md` (comprehensive guide)
- **Database Setup:** `DATABASE_SETUP.md` (detailed setup)
- **Microsoft Docs:** https://learn.microsoft.com/azure/azure-functions/
- **ODBC Driver:** https://learn.microsoft.com/sql/connect/odbc/

## ✅ Success Metrics

After deployment, you should see:
- ✓ Schema created with 5 tables
- ✓ 10 categories pre-seeded
- ✓ Initial data: ~1,200 records
- ✓ Daily additions: ~500 records
- ✓ Function running on schedule
- ✓ No errors in Application Insights
- ✓ Growing dataset for testing

---

**Last Updated:** October 2025  
**Version:** 1.0  
**Database:** <your-sql-server>.database.windows.net
