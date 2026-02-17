-- ========================================
-- SQL Server Row-Level Security (RLS) Implementation
-- Database: Azure SQL / Fabric SQL
-- Purpose: Enforce data access control at database level
-- ========================================

-- Enable RLS on the database
-- This creates security infrastructure for row-level filtering

PRINT '🔐 Implementing Row-Level Security (RLS) Policies...';
GO

-- ========================================
-- Step 1: Create Security Schema
-- ========================================
IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'Security')
BEGIN
    EXEC('CREATE SCHEMA Security');
    PRINT '✅ Security schema created';
END
GO

-- ========================================
-- Step 2: Create Security Context Functions
-- ========================================

-- Function to get current user's ID from SESSION_CONTEXT
CREATE OR ALTER FUNCTION Security.fn_GetCurrentUserId()
RETURNS INT
AS
BEGIN
    RETURN CAST(SESSION_CONTEXT(N'UserId') AS INT);
END;
GO

-- Function to get current user's region(s) from SESSION_CONTEXT
CREATE OR ALTER FUNCTION Security.fn_GetCurrentUserRegion()
RETURNS NVARCHAR(MAX)
AS
BEGIN
    RETURN CAST(SESSION_CONTEXT(N'UserRegion') AS NVARCHAR(MAX));
END;
GO

-- Function to get current user's roles from SESSION_CONTEXT
CREATE OR ALTER FUNCTION Security.fn_GetCurrentUserRoles()
RETURNS NVARCHAR(MAX)
AS
BEGIN
    RETURN CAST(SESSION_CONTEXT(N'UserRoles') AS NVARCHAR(MAX));
END;
GO

-- Function to check if user is admin
CREATE OR ALTER FUNCTION Security.fn_IsAdmin()
RETURNS BIT
AS
BEGIN
    DECLARE @Roles NVARCHAR(MAX) = Security.fn_GetCurrentUserRoles();
    IF @Roles IS NULL RETURN 0;
    
    -- Check if user has Admin or SuperAdmin role
    IF @Roles LIKE '%Admin%' OR @Roles LIKE '%SuperAdmin%'
        RETURN 1;
    
    RETURN 0;
END;
GO

-- ========================================
-- Step 3: Create RLS Predicate Functions
-- ========================================

-- Predicate for Sales data filtering by region
CREATE OR ALTER FUNCTION Security.fn_SalesRegionPredicate(@Region NVARCHAR(50))
RETURNS TABLE
WITH SCHEMABINDING
AS
RETURN
    SELECT 1 AS AccessGranted
    WHERE 
        -- Grant access if user is admin
        Security.fn_IsAdmin() = 1
        OR
        -- Grant access if region matches user's assigned region
        @Region = Security.fn_GetCurrentUserRegion()
        OR
        -- Grant access if no region specified (public data)
        @Region IS NULL
        OR
        -- Grant access if no user context (system queries)
        Security.fn_GetCurrentUserId() IS NULL;
GO

-- Predicate for Customer data filtering
CREATE OR ALTER FUNCTION Security.fn_CustomerAccessPredicate(@CustomerID INT)
RETURNS TABLE
WITH SCHEMABINDING
AS
RETURN
    SELECT 1 AS AccessGranted
    WHERE
        -- Admins see all customers
        Security.fn_IsAdmin() = 1
        OR
        -- Users see customers in their assigned territories
        EXISTS (
            SELECT 1 
            FROM Security.UserCustomerAssignments uca
            WHERE uca.UserID = Security.fn_GetCurrentUserId()
                AND uca.CustomerID = @CustomerID
                AND uca.IsActive = 1
        )
        OR
        -- System queries (no user context)
        Security.fn_GetCurrentUserId() IS NULL;
GO

-- Predicate for Employee/Hierarchy filtering
CREATE OR ALTER FUNCTION Security.fn_EmployeeAccessPredicate(@EmployeeID INT)
RETURNS TABLE
WITH SCHEMABINDING
AS
RETURN
    SELECT 1 AS AccessGranted
    WHERE
        -- Admins see all employees
        Security.fn_IsAdmin() = 1
        OR
        -- Users see themselves
        @EmployeeID = Security.fn_GetCurrentUserId()
        OR
        -- Managers see their direct reports and sub-reports
        EXISTS (
            SELECT 1
            FROM Security.OrganizationHierarchy oh
            WHERE oh.ManagerID = Security.fn_GetCurrentUserId()
                AND oh.EmployeeID = @EmployeeID
                AND oh.IsActive = 1
        )
        OR
        -- System queries
        Security.fn_GetCurrentUserId() IS NULL;
GO

-- ========================================
-- Step 4: Create Supporting Tables for RLS
-- ========================================

-- User Territory Assignments
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'UserTerritories' AND schema_id = SCHEMA_ID('Security'))
BEGIN
    CREATE TABLE Security.UserTerritories (
        UserTerritoryID INT IDENTITY(1,1) PRIMARY KEY,
        UserID INT NOT NULL,
        Territory NVARCHAR(50) NOT NULL,
        Region NVARCHAR(50) NOT NULL,
        IsActive BIT DEFAULT 1,
        AssignedDate DATETIME2 DEFAULT GETUTCDATE(),
        AssignedBy INT,
        CONSTRAINT FK_UserTerritories_User FOREIGN KEY (UserID) REFERENCES dbo.Users(UserID)
    );
    
    CREATE INDEX IX_UserTerritories_UserID ON Security.UserTerritories(UserID);
    CREATE INDEX IX_UserTerritories_Territory ON Security.UserTerritories(Territory);
    
    PRINT '✅ UserTerritories table created';
END
GO

-- User Customer Assignments
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'UserCustomerAssignments' AND schema_id = SCHEMA_ID('Security'))
BEGIN
    CREATE TABLE Security.UserCustomerAssignments (
        AssignmentID INT IDENTITY(1,1) PRIMARY KEY,
        UserID INT NOT NULL,
        CustomerID INT NOT NULL,
        IsActive BIT DEFAULT 1,
        AssignedDate DATETIME2 DEFAULT GETUTCDATE(),
        AssignedBy INT,
        CONSTRAINT FK_UserCustomerAssignments_User FOREIGN KEY (UserID) REFERENCES dbo.Users(UserID)
    );
    
    CREATE INDEX IX_UserCustomerAssignments_UserID ON Security.UserCustomerAssignments(UserID);
    CREATE INDEX IX_UserCustomerAssignments_CustomerID ON Security.UserCustomerAssignments(CustomerID);
    
    PRINT '✅ UserCustomerAssignments table created';
END
GO

-- Organization Hierarchy
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'OrganizationHierarchy' AND schema_id = SCHEMA_ID('Security'))
BEGIN
    CREATE TABLE Security.OrganizationHierarchy (
        HierarchyID INT IDENTITY(1,1) PRIMARY KEY,
        EmployeeID INT NOT NULL,
        ManagerID INT NOT NULL,
        Level INT DEFAULT 1,
        IsActive BIT DEFAULT 1,
        EffectiveDate DATETIME2 DEFAULT GETUTCDATE(),
        CONSTRAINT FK_OrganizationHierarchy_Employee FOREIGN KEY (EmployeeID) REFERENCES dbo.Users(UserID),
        CONSTRAINT FK_OrganizationHierarchy_Manager FOREIGN KEY (ManagerID) REFERENCES dbo.Users(UserID)
    );
    
    CREATE INDEX IX_OrganizationHierarchy_EmployeeID ON Security.OrganizationHierarchy(EmployeeID);
    CREATE INDEX IX_OrganizationHierarchy_ManagerID ON Security.OrganizationHierarchy(ManagerID);
    
    PRINT '✅ OrganizationHierarchy table created';
END
GO

-- Data Access Audit Log
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'DataAccessLog' AND schema_id = SCHEMA_ID('Security'))
BEGIN
    CREATE TABLE Security.DataAccessLog (
        LogID INT IDENTITY(1,1) PRIMARY KEY,
        UserID INT NOT NULL,
        Username NVARCHAR(100),
        AccessType NVARCHAR(50) NOT NULL, -- 'Query', 'Chat', 'PowerBI', 'API'
        TableAccessed NVARCHAR(100),
        QueryText NVARCHAR(MAX),
        RowsReturned INT,
        SessionID NVARCHAR(100),
        ClientIP NVARCHAR(50),
        UserAgent NVARCHAR(500),
        Timestamp DATETIME2 DEFAULT GETUTCDATE(),
        RLSFilterApplied NVARCHAR(500)
    );
    
    CREATE INDEX IX_DataAccessLog_UserID ON Security.DataAccessLog(UserID);
    CREATE INDEX IX_DataAccessLog_Timestamp ON Security.DataAccessLog(Timestamp);
    CREATE INDEX IX_DataAccessLog_AccessType ON Security.DataAccessLog(AccessType);
    
    PRINT '✅ DataAccessLog table created';
END
GO

-- ========================================
-- Step 5: Create Stored Procedures for Session Context
-- ========================================

-- Set user context at session start
CREATE OR ALTER PROCEDURE Security.usp_SetUserContext
    @UserId INT,
    @Username NVARCHAR(100),
    @UserEmail NVARCHAR(255),
    @UserRoles NVARCHAR(MAX),
    @UserRegion NVARCHAR(50) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Set session context variables (available for RLS predicates)
    EXEC sp_set_session_context @key = N'UserId', @value = @UserId;
    EXEC sp_set_session_context @key = N'Username', @value = @Username;
    EXEC sp_set_session_context @key = N'UserEmail', @value = @UserEmail;
    EXEC sp_set_session_context @key = N'UserRoles', @value = @UserRoles;
    
    -- Get user's primary region if not provided
    IF @UserRegion IS NULL
    BEGIN
        SELECT TOP 1 @UserRegion = Territory
        FROM Security.UserTerritories
        WHERE UserID = @UserId AND IsActive = 1
        ORDER BY AssignedDate DESC;
    END
    
    EXEC sp_set_session_context @key = N'UserRegion', @value = @UserRegion;
    
    -- Log context setting
    PRINT '✅ Session context set for user: ' + @Username + ' (Region: ' + ISNULL(@UserRegion, 'None') + ')';
END;
GO

-- Log data access
CREATE OR ALTER PROCEDURE Security.usp_LogDataAccess
    @UserID INT,
    @Username NVARCHAR(100),
    @AccessType NVARCHAR(50),
    @TableAccessed NVARCHAR(100) = NULL,
    @QueryText NVARCHAR(MAX) = NULL,
    @RowsReturned INT = NULL,
    @SessionID NVARCHAR(100) = NULL,
    @ClientIP NVARCHAR(50) = NULL,
    @UserAgent NVARCHAR(500) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    INSERT INTO Security.DataAccessLog (
        UserID, Username, AccessType, TableAccessed,
        QueryText, RowsReturned, SessionID, ClientIP, UserAgent,
        RLSFilterApplied
    )
    VALUES (
        @UserID, @Username, @AccessType, @TableAccessed,
        @QueryText, @RowsReturned, @SessionID, @ClientIP, @UserAgent,
        'Region: ' + CAST(SESSION_CONTEXT(N'UserRegion') AS NVARCHAR(50))
    );
END;
GO

-- ========================================
-- Step 6: Apply Security Policies (COMMENTED OUT)
-- Uncomment after adding Region column to your tables
-- ========================================

/*
-- Example: Apply RLS to Sales table
IF EXISTS (SELECT * FROM sys.tables WHERE name = 'Sales' AND schema_id = SCHEMA_ID('dbo'))
BEGIN
    -- Drop existing policy if it exists
    IF EXISTS (SELECT * FROM sys.security_policies WHERE name = 'SalesRegionSecurityPolicy')
    BEGIN
        ALTER SECURITY POLICY Security.SalesRegionSecurityPolicy DROP FILTER PREDICATE ON dbo.Sales;
        DROP SECURITY POLICY Security.SalesRegionSecurityPolicy;
    END
    
    -- Create new security policy
    CREATE SECURITY POLICY Security.SalesRegionSecurityPolicy
    ADD FILTER PREDICATE Security.fn_SalesRegionPredicate(Region) ON dbo.Sales
    WITH (STATE = ON);
    
    PRINT '✅ RLS policy applied to Sales table';
END

-- Example: Apply RLS to Customers table
IF EXISTS (SELECT * FROM sys.tables WHERE name = 'Customers' AND schema_id = SCHEMA_ID('dbo'))
BEGIN
    IF EXISTS (SELECT * FROM sys.security_policies WHERE name = 'CustomerSecurityPolicy')
    BEGIN
        ALTER SECURITY POLICY Security.CustomerSecurityPolicy DROP FILTER PREDICATE ON dbo.Customers;
        DROP SECURITY POLICY Security.CustomerSecurityPolicy;
    END
    
    CREATE SECURITY POLICY Security.CustomerSecurityPolicy
    ADD FILTER PREDICATE Security.fn_CustomerAccessPredicate(CustomerID) ON dbo.Customers
    WITH (STATE = ON);
    
    PRINT '✅ RLS policy applied to Customers table';
END

-- Example: Apply RLS to Orders table
IF EXISTS (SELECT * FROM sys.tables WHERE name = 'Orders' AND schema_id = SCHEMA_ID('dbo'))
BEGIN
    IF EXISTS (SELECT * FROM sys.security_policies WHERE name = 'OrderSecurityPolicy')
    BEGIN
        ALTER SECURITY POLICY Security.OrderSecurityPolicy DROP FILTER PREDICATE ON dbo.Orders;
        DROP SECURITY POLICY Security.OrderSecurityPolicy;
    END
    
    -- Assuming Orders has CustomerID
    CREATE SECURITY POLICY Security.OrderSecurityPolicy
    ADD FILTER PREDICATE Security.fn_CustomerAccessPredicate(CustomerID) ON dbo.Orders
    WITH (STATE = ON);
    
    PRINT '✅ RLS policy applied to Orders table';
END
*/

-- ========================================
-- Step 7: Insert Sample Territory Assignments
-- ========================================

-- Assign territories to users (run after users are created)
-- Example:
/*
INSERT INTO Security.UserTerritories (UserID, Territory, Region)
VALUES 
    (2, 'West', 'USA-West'),
    (3, 'East', 'USA-East'),
    (4, 'Central', 'USA-Central');
*/

PRINT '⚠️  TODO: Assign territories to users after user creation';
PRINT '⚠️  TODO: Uncomment and customize security policies for your tables';

GO

-- ========================================
-- Step 8: Testing and Validation
-- ========================================

-- Test setting session context
PRINT '🧪 Testing session context...';

EXEC Security.usp_SetUserContext 
    @UserId = 999,
    @Username = 'testuser',
    @UserEmail = 'test@example.com',
    @UserRoles = 'User',
    @UserRegion = 'West';

-- Verify session context
SELECT 
    CAST(SESSION_CONTEXT(N'UserId') AS INT) AS UserId,
    CAST(SESSION_CONTEXT(N'Username') AS NVARCHAR(100)) AS Username,
    CAST(SESSION_CONTEXT(N'UserRegion') AS NVARCHAR(50)) AS UserRegion,
    CAST(SESSION_CONTEXT(N'UserRoles') AS NVARCHAR(MAX)) AS UserRoles;

PRINT '✅ Session context test completed';
GO

-- ========================================
-- Summary and Next Steps
-- ========================================

PRINT '';
PRINT '========================================';
PRINT '✅ RLS Infrastructure Created Successfully!';
PRINT '========================================';
PRINT '';
PRINT 'Next Steps:';
PRINT '1. Add Region/CustomerID columns to your tables if not present';
PRINT '2. Uncomment and customize security policies (Step 6)';
PRINT '3. Assign users to territories using UserTerritories table';
PRINT '4. Test RLS with different user contexts';
PRINT '5. Update application code to call usp_SetUserContext on each connection';
PRINT '';
PRINT 'Verification Queries:';
PRINT '- SELECT * FROM Security.UserTerritories;';
PRINT '- SELECT * FROM Security.DataAccessLog;';
PRINT '- SELECT * FROM sys.security_policies;';
PRINT '';
PRINT '⚠️  IMPORTANT: RLS policies are NOT active until you:';
PRINT '   1. Add Region columns to your tables';
PRINT '   2. Uncomment security policies in Step 6';
PRINT '   3. Set STATE = ON for each policy';
PRINT '';
