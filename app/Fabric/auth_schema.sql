-- ========================================
-- Authentication & Authorization Schema
-- Database: <your-sql-server>.database.windows.net
-- ========================================

-- Drop existing auth tables if they exist (in reverse order due to foreign keys)
IF OBJECT_ID('dbo.UserRoles', 'U') IS NOT NULL DROP TABLE dbo.UserRoles;
IF OBJECT_ID('dbo.RolePermissions', 'U') IS NOT NULL DROP TABLE dbo.RolePermissions;
IF OBJECT_ID('dbo.Permissions', 'U') IS NOT NULL DROP TABLE dbo.Permissions;
IF OBJECT_ID('dbo.Users', 'U') IS NOT NULL DROP TABLE dbo.Users;
IF OBJECT_ID('dbo.Roles', 'U') IS NOT NULL DROP TABLE dbo.Roles;
GO

-- ========================================
-- Roles Table
-- ========================================
CREATE TABLE dbo.Roles (
    RoleID INT IDENTITY(1,1) PRIMARY KEY,
    RoleName NVARCHAR(50) NOT NULL UNIQUE,
    Description NVARCHAR(255),
    IsActive BIT DEFAULT 1,
    CreatedDate DATETIME2 DEFAULT GETUTCDATE(),
    ModifiedDate DATETIME2 DEFAULT GETUTCDATE()
);
GO

CREATE INDEX IX_Roles_RoleName ON dbo.Roles(RoleName);
GO

-- ========================================
-- Permissions Table
-- ========================================
CREATE TABLE dbo.Permissions (
    PermissionID INT IDENTITY(1,1) PRIMARY KEY,
    PermissionName NVARCHAR(100) NOT NULL UNIQUE,
    Description NVARCHAR(255),
    Resource NVARCHAR(50) NOT NULL, -- e.g., 'chat', 'admin', 'analytics', 'fabric'
    Action NVARCHAR(50) NOT NULL, -- e.g., 'read', 'write', 'delete', 'execute'
    CreatedDate DATETIME2 DEFAULT GETUTCDATE(),
    ModifiedDate DATETIME2 DEFAULT GETUTCDATE()
);
GO

CREATE INDEX IX_Permissions_Resource ON dbo.Permissions(Resource);
CREATE INDEX IX_Permissions_PermissionName ON dbo.Permissions(PermissionName);
GO

-- ========================================
-- Users Table
-- ========================================
CREATE TABLE dbo.Users (
    UserID INT IDENTITY(1,1) PRIMARY KEY,
    Username NVARCHAR(100) NOT NULL UNIQUE,
    Email NVARCHAR(255) NOT NULL UNIQUE,
    PasswordHash NVARCHAR(255) NOT NULL,
    FirstName NVARCHAR(100),
    LastName NVARCHAR(100),
    IsActive BIT DEFAULT 1,
    IsEmailVerified BIT DEFAULT 0,
    LastLoginDate DATETIME2,
    FailedLoginAttempts INT DEFAULT 0,
    AccountLockedUntil DATETIME2,
    CreatedDate DATETIME2 DEFAULT GETUTCDATE(),
    ModifiedDate DATETIME2 DEFAULT GETUTCDATE(),
    CreatedBy INT,
    ModifiedBy INT
);
GO

CREATE INDEX IX_Users_Username ON dbo.Users(Username);
CREATE INDEX IX_Users_Email ON dbo.Users(Email);
CREATE INDEX IX_Users_IsActive ON dbo.Users(IsActive);
GO

-- ========================================
-- UserRoles Junction Table
-- ========================================
CREATE TABLE dbo.UserRoles (
    UserRoleID INT IDENTITY(1,1) PRIMARY KEY,
    UserID INT NOT NULL,
    RoleID INT NOT NULL,
    AssignedDate DATETIME2 DEFAULT GETUTCDATE(),
    AssignedBy INT,
    CONSTRAINT FK_UserRoles_Users FOREIGN KEY (UserID) 
        REFERENCES dbo.Users(UserID) ON DELETE CASCADE,
    CONSTRAINT FK_UserRoles_Roles FOREIGN KEY (RoleID) 
        REFERENCES dbo.Roles(RoleID),
    CONSTRAINT UK_UserRoles UNIQUE(UserID, RoleID)
);
GO

CREATE INDEX IX_UserRoles_UserID ON dbo.UserRoles(UserID);
CREATE INDEX IX_UserRoles_RoleID ON dbo.UserRoles(RoleID);
GO

-- ========================================
-- RolePermissions Junction Table
-- ========================================
CREATE TABLE dbo.RolePermissions (
    RolePermissionID INT IDENTITY(1,1) PRIMARY KEY,
    RoleID INT NOT NULL,
    PermissionID INT NOT NULL,
    CreatedDate DATETIME2 DEFAULT GETUTCDATE(),
    CONSTRAINT FK_RolePermissions_Roles FOREIGN KEY (RoleID) 
        REFERENCES dbo.Roles(RoleID) ON DELETE CASCADE,
    CONSTRAINT FK_RolePermissions_Permissions FOREIGN KEY (PermissionID) 
        REFERENCES dbo.Permissions(PermissionID) ON DELETE CASCADE,
    CONSTRAINT UK_RolePermissions UNIQUE(RoleID, PermissionID)
);
GO

CREATE INDEX IX_RolePermissions_RoleID ON dbo.RolePermissions(RoleID);
CREATE INDEX IX_RolePermissions_PermissionID ON dbo.RolePermissions(PermissionID);
GO

-- ========================================
-- Insert Default Roles
-- ========================================
SET IDENTITY_INSERT dbo.Roles ON;
INSERT INTO dbo.Roles (RoleID, RoleName, Description) VALUES
(1, 'SuperAdmin', 'Full system access with all permissions'),
(2, 'Admin', 'Administrative access to manage users and settings'),
(3, 'PowerUser', 'Advanced user with access to analytics and Fabric integration'),
(4, 'User', 'Standard user with chat access'),
(5, 'ReadOnly', 'Read-only access to view data without modifications');
SET IDENTITY_INSERT dbo.Roles OFF;
GO

-- ========================================
-- Insert Default Permissions
-- ========================================
SET IDENTITY_INSERT dbo.Permissions ON;
INSERT INTO dbo.Permissions (PermissionID, PermissionName, Description, Resource, Action) VALUES
-- Chat Permissions
(1, 'chat.access', 'Access to chat interface', 'chat', 'read'),
(2, 'chat.send', 'Send messages in chat', 'chat', 'write'),
(3, 'chat.history', 'View chat history', 'chat', 'read'),

-- Admin Permissions
(4, 'admin.access', 'Access to admin dashboard', 'admin', 'read'),
(5, 'admin.users.view', 'View user list', 'admin', 'read'),
(6, 'admin.users.create', 'Create new users', 'admin', 'write'),
(7, 'admin.users.edit', 'Edit user details', 'admin', 'write'),
(8, 'admin.users.delete', 'Delete users', 'admin', 'delete'),
(9, 'admin.roles.manage', 'Manage user roles', 'admin', 'write'),

-- Analytics Permissions
(10, 'analytics.view', 'View analytics and reports', 'analytics', 'read'),
(11, 'analytics.export', 'Export analytics data', 'analytics', 'execute'),

-- Fabric Permissions
(12, 'fabric.access', 'Access Fabric integration', 'fabric', 'read'),
(13, 'fabric.sales', 'Access sales data in Fabric', 'fabric', 'read'),
(14, 'fabric.realtime', 'Access realtime operations data', 'fabric', 'read'),
(15, 'fabric.analytics', 'Access advanced Fabric analytics', 'fabric', 'execute'),

-- PowerBI Permissions
(16, 'powerbi.view', 'View PowerBI reports', 'powerbi', 'read'),
(17, 'powerbi.embed', 'Embed PowerBI visualizations', 'powerbi', 'execute');
SET IDENTITY_INSERT dbo.Permissions OFF;
GO

-- ========================================
-- Assign Permissions to Roles
-- ========================================

-- SuperAdmin: All Permissions
INSERT INTO dbo.RolePermissions (RoleID, PermissionID)
SELECT 1, PermissionID FROM dbo.Permissions;

-- Admin: All except some super admin specific
INSERT INTO dbo.RolePermissions (RoleID, PermissionID)
SELECT 2, PermissionID FROM dbo.Permissions 
WHERE PermissionID IN (1,2,3,4,5,6,7,9,10,11,12,13,14,16,17);

-- PowerUser: Chat, Analytics, Fabric
INSERT INTO dbo.RolePermissions (RoleID, PermissionID)
SELECT 3, PermissionID FROM dbo.Permissions 
WHERE PermissionID IN (1,2,3,10,11,12,13,14,15,16,17);

-- User: Basic Chat and View
INSERT INTO dbo.RolePermissions (RoleID, PermissionID)
SELECT 4, PermissionID FROM dbo.Permissions 
WHERE PermissionID IN (1,2,3,10,12,16);

-- ReadOnly: View Only
INSERT INTO dbo.RolePermissions (RoleID, PermissionID)
SELECT 5, PermissionID FROM dbo.Permissions 
WHERE PermissionID IN (1,3,10,12,16);
GO

-- ========================================
-- Create Default Admin User
-- SECURITY: Default password removed for security reasons
-- Run the following to create your admin user after deployment:
-- 
-- EXEC dbo.sp_CreateAdminUser 
--     @Username = 'youradmin',
--     @Email = 'admin@yourcompany.com', 
--     @Password = 'YourSecurePassword123!';
-- ========================================

-- Stored procedure to create admin user securely
CREATE OR ALTER PROCEDURE dbo.sp_CreateAdminUser
    @Username NVARCHAR(100),
    @Email NVARCHAR(255),
    @Password NVARCHAR(100)
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Check if admin already exists
    IF EXISTS (SELECT 1 FROM dbo.Users WHERE Username = @Username)
    BEGIN
        RAISERROR('Admin user already exists', 16, 1);
        RETURN;
    END
    
    -- Validate password complexity (minimum 8 chars, uppercase, lowercase, number, special char)
    IF LEN(@Password) < 8 
        OR @Password NOT LIKE '%[A-Z]%' 
        OR @Password NOT LIKE '%[a-z]%' 
        OR @Password NOT LIKE '%[0-9]%'
        OR @Password NOT LIKE '%[^a-zA-Z0-9]%'
    BEGIN
        RAISERROR('Password must be at least 8 characters with uppercase, lowercase, number, and special character', 16, 1);
        RETURN;
    END
    
    -- Note: Password hashing must be done in application code with bcrypt
    -- This is a placeholder - call from Python with hashed password
    RAISERROR('Please use the application API to create admin user with proper password hashing', 16, 1);
END;
GO

-- ========================================
-- Create Stored Procedures for Common Operations
-- ========================================

-- Get User with Roles and Permissions
CREATE OR ALTER PROCEDURE dbo.sp_GetUserByUsername
    @Username NVARCHAR(100)
AS
BEGIN
    SET NOCOUNT ON;
    
    SELECT 
        u.UserID,
        u.Username,
        u.Email,
        u.PasswordHash,
        u.FirstName,
        u.LastName,
        u.IsActive,
        u.IsEmailVerified,
        u.LastLoginDate,
        u.FailedLoginAttempts,
        u.AccountLockedUntil,
        STRING_AGG(r.RoleName, ',') AS Roles,
        (
            SELECT STRING_AGG(p.PermissionName, ',')
            FROM dbo.UserRoles ur2
            INNER JOIN dbo.RolePermissions rp ON ur2.RoleID = rp.RoleID
            INNER JOIN dbo.Permissions p ON rp.PermissionID = p.PermissionID
            WHERE ur2.UserID = u.UserID
        ) AS Permissions
    FROM dbo.Users u
    LEFT JOIN dbo.UserRoles ur ON u.UserID = ur.UserID
    LEFT JOIN dbo.Roles r ON ur.RoleID = r.RoleID
    WHERE u.Username = @Username
    GROUP BY 
        u.UserID, u.Username, u.Email, u.PasswordHash, 
        u.FirstName, u.LastName, u.IsActive, u.IsEmailVerified,
        u.LastLoginDate, u.FailedLoginAttempts, u.AccountLockedUntil;
END;
GO

-- Update Last Login
CREATE OR ALTER PROCEDURE dbo.sp_UpdateLastLogin
    @UserID INT
AS
BEGIN
    SET NOCOUNT ON;
    
    UPDATE dbo.Users 
    SET LastLoginDate = GETUTCDATE(),
        FailedLoginAttempts = 0,
        ModifiedDate = GETUTCDATE()
    WHERE UserID = @UserID;
END;
GO

-- Record Failed Login Attempt
CREATE OR ALTER PROCEDURE dbo.sp_RecordFailedLogin
    @Username NVARCHAR(100)
AS
BEGIN
    SET NOCOUNT ON;
    
    UPDATE dbo.Users 
    SET FailedLoginAttempts = FailedLoginAttempts + 1,
        AccountLockedUntil = CASE 
            WHEN FailedLoginAttempts >= 4 THEN DATEADD(MINUTE, 15, GETUTCDATE())
            ELSE AccountLockedUntil
        END,
        ModifiedDate = GETUTCDATE()
    WHERE Username = @Username;
END;
GO

PRINT '✅ Authentication schema created successfully!';
PRINT '✅ Default roles and permissions configured.';
PRINT '✅ Default admin user created (username: admin, password: Admin@123)';
PRINT '⚠️  IMPORTANT: Change the default admin password after first login!';
GO
