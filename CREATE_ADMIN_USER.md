# Creating Admin User - Secure Setup Guide

## Overview

For security reasons, the default admin user with password `Admin@123` has been **REMOVED** from the deployment scripts. You must create your admin user manually after database deployment.

## Prerequisites

1. Database schema deployed (`auth_schema.sql`)
2. Application running with authentication enabled
3. Access to the application API

---

## Method 1: Using Python Script (Recommended)

Create a file `create_admin.py`:

```python
import requests
import bcrypt

# Configuration
API_URL = "http://localhost:8080"  # Change to your deployment URL
ADMIN_USERNAME = "admin"
ADMIN_EMAIL = "admin@yourcompany.com"
ADMIN_PASSWORD = "YourSecurePassword123!"  # Change this!

# Validate password complexity
if len(ADMIN_PASSWORD) < 8:
    print("❌ Password must be at least 8 characters")
    exit(1)

if not any(c.isupper() for c in ADMIN_PASSWORD):
    print("❌ Password must contain uppercase letter")
    exit(1)

if not any(c.islower() for c in ADMIN_PASSWORD):
    print("❌ Password must contain lowercase letter")
    exit(1)

if not any(c.isdigit() for c in ADMIN_PASSWORD):
    print("❌ Password must contain number")
    exit(1)

if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in ADMIN_PASSWORD):
    print("❌ Password must contain special character")
    exit(1)

print("✅ Password complexity validated")

# Create admin user via API (you'll need to add this endpoint)
print(f"Creating admin user: {ADMIN_USERNAME}")

# For now, you need to insert directly into database with hashed password
# This requires database access

print("""
To create admin user, run this SQL:

SET IDENTITY_INSERT dbo.Users ON;

INSERT INTO dbo.Users (UserID, Username, Email, PasswordHash, FirstName, LastName, IsActive, IsEmailVerified)
VALUES (1, '{username}', '{email}', 
        '{password_hash}', 
        'System', 'Administrator', 1, 1);

SET IDENTITY_INSERT dbo.Users OFF;

-- Assign SuperAdmin role
INSERT INTO dbo.UserRoles (UserID, RoleID) VALUES (1, 1);
""".format(
    username=ADMIN_USERNAME,
    email=ADMIN_EMAIL,
    password_hash=bcrypt.hashpw(ADMIN_PASSWORD.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
))

print("\n⚠️  IMPORTANT: Save these credentials securely!")
print(f"Username: {ADMIN_USERNAME}")
print(f"Email: {ADMIN_EMAIL}")
print("Password: <stored securely - do not log>")
```

Run the script:
```bash
python create_admin.py
```

---

## Method 2: Direct SQL Insert (Database Access Required)

### Step 1: Generate Password Hash

Use Python to hash your password:

```python
import bcrypt

password = "YourSecurePassword123!"  # Change this!
hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
print(hashed.decode('utf-8'))
```

### Step 2: Insert into Database

Connect to your Azure SQL Database and run:

```sql
-- Replace placeholders with your values
DECLARE @Username NVARCHAR(100) = 'youradmin';
DECLARE @Email NVARCHAR(255) = 'admin@yourcompany.com';
DECLARE @PasswordHash NVARCHAR(255) = '<paste_bcrypt_hash_here>';

-- Insert admin user
SET IDENTITY_INSERT dbo.Users ON;

INSERT INTO dbo.Users (UserID, Username, Email, PasswordHash, FirstName, LastName, IsActive, IsEmailVerified)
VALUES (1, @Username, @Email, @PasswordHash, 'System', 'Administrator', 1, 1);

SET IDENTITY_INSERT dbo.Users OFF;

-- Assign SuperAdmin role (RoleID = 1)
INSERT INTO dbo.UserRoles (UserID, RoleID) 
VALUES (1, 1);

-- Verify creation
SELECT u.UserID, u.Username, u.Email, r.RoleName
FROM dbo.Users u
LEFT JOIN dbo.UserRoles ur ON u.UserID = ur.UserID
LEFT JOIN dbo.Roles r ON ur.RoleID = r.RoleID
WHERE u.Username = @Username;
```

---

## Method 3: Using Azure CLI and sqlcmd

```bash
# Set variables
USERNAME="youradmin"
EMAIL="admin@yourcompany.com"
PASSWORD="YourSecurePassword123!"
SERVER="your-sql-server.database.windows.net"
DATABASE="aiagentsdb"

# Generate password hash (requires Python)
HASH=$(python -c "import bcrypt; print(bcrypt.hashpw('$PASSWORD'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8'))")

# Connect and insert
sqlcmd -S $SERVER -d $DATABASE -G -Q "
SET IDENTITY_INSERT dbo.Users ON;
INSERT INTO dbo.Users (UserID, Username, Email, PasswordHash, FirstName, LastName, IsActive, IsEmailVerified)
VALUES (1, '$USERNAME', '$EMAIL', '$HASH', 'System', 'Administrator', 1, 1);
SET IDENTITY_INSERT dbo.Users OFF;
INSERT INTO dbo.UserRoles (UserID, RoleID) VALUES (1, 1);
"
```

---

## Password Requirements

Your admin password MUST meet these requirements:

- ✅ Minimum 8 characters
- ✅ At least one uppercase letter (A-Z)
- ✅ At least one lowercase letter (a-z)
- ✅ At least one number (0-9)
- ✅ At least one special character (!@#$%^&*()_+-=[]{}|;:,.<>?)

**Examples of STRONG passwords:**
- `MyC0mpany@2026!`
- `Adm1n$SecurePass`
- `P@ssw0rd2026!Admin`

**Examples of WEAK passwords (DO NOT USE):**
- `Admin@123` (too common, compromised)
- `password` (no complexity)
- `12345678` (no letters)
- `AdminPassword` (no numbers/symbols)

---

## Security Best Practices

### 1. Change Password on First Login

Add this to your first login workflow:

```python
@auth_router.post("/first-login-password-change")
async def first_login_password_change(
    current_password: str,
    new_password: str,
    current_user: dict = Depends(get_current_user)
):
    # Force password change for admin on first login
    # Mark as password_changed in database
    pass
```

### 2. Enable Multi-Factor Authentication (MFA)

For admin accounts, implement MFA:
- TOTP (Time-based One-Time Password)
- SMS verification
- Email verification

### 3. Audit Admin Actions

Log all admin operations:
```sql
CREATE TABLE dbo.AdminAuditLog (
    AuditID INT IDENTITY(1,1) PRIMARY KEY,
    AdminUserID INT NOT NULL,
    Action NVARCHAR(100) NOT NULL,
    TargetUser INT,
    Timestamp DATETIME2 DEFAULT GETUTCDATE(),
    IPAddress NVARCHAR(50),
    Success BIT
);
```

### 4. Regular Password Rotation

Implement password expiration:
```sql
ALTER TABLE dbo.Users ADD PasswordExpiryDate DATETIME2;

-- Set 90-day expiry for admin
UPDATE dbo.Users 
SET PasswordExpiryDate = DATEADD(DAY, 90, GETUTCDATE())
WHERE UserID = 1;
```

---

## Troubleshooting

### "Admin user already exists"

If you get this error, check existing users:

```sql
SELECT UserID, Username, Email, IsActive 
FROM dbo.Users 
WHERE RoleID IN (SELECT RoleID FROM dbo.Roles WHERE RoleName = 'SuperAdmin');
```

To reset the admin user:

```sql
-- Delete existing admin
DELETE FROM dbo.UserRoles WHERE UserID = 1;
DELETE FROM dbo.Users WHERE UserID = 1;

-- Recreate with new credentials
-- (follow steps above)
```

### "Cannot insert duplicate key"

If UserID = 1 already exists:

```sql
-- Find next available ID
SELECT MAX(UserID) + 1 FROM dbo.Users;

-- Use that ID instead of forcing identity insert
```

### "Authentication failed"

Verify password hash is correct:

```python
import bcrypt

# Test password verification
stored_hash = "<hash_from_database>"
test_password = "YourPassword123!"

if bcrypt.checkpw(test_password.encode('utf-8'), stored_hash.encode('utf-8')):
    print("✅ Password matches!")
else:
    print("❌ Password does not match!")
```

---

## Verification

After creating the admin user, test authentication:

```bash
# Test login
curl -X POST http://localhost:8080/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "youradmin",
    "password": "YourSecurePassword123!"
  }'

# Should return:
# {
#   "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
#   "token_type": "bearer",
#   "user": {
#     "user_id": 1,
#     "username": "youradmin",
#     "roles": ["SuperAdmin"]
#   }
# }
```

---

## Next Steps

1. ✅ Create admin user using one of the methods above
2. ✅ Test login and verify SuperAdmin role
3. ✅ Change password immediately after first login
4. ✅ Enable MFA for admin account
5. ✅ Create additional admin users with principle of least privilege
6. ✅ Document admin credentials in secure vault (Azure Key Vault, 1Password, etc.)

---

## Security Checklist

- [ ] Admin password meets complexity requirements
- [ ] Admin password is unique (not reused from other systems)
- [ ] Admin credentials stored in secure vault
- [ ] Password changed on first login
- [ ] MFA enabled for admin account
- [ ] Admin actions are logged and audited
- [ ] Regular password rotation policy implemented
- [ ] Backup admin account created (in case of lockout)

---

**Last Updated:** January 30, 2026  
**Security Level:** Critical - Handle with Care
