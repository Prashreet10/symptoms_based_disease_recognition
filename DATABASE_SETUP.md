# MySQL Database Setup Guide

This guide will help you set up MySQL database connectivity for the Symptom-based Disease Prediction application.

## Prerequisites

1. **MySQL Server** - Download and install from [mysql.com](https://www.mysql.com/downloads/)
   - Windows: MySQL Community Server MSI Installer
   - macOS: Homebrew or DMG Installer
   - Linux: Package manager (apt, yum, etc.)

2. **Python 3.7+** - Already installed on your system

## Installation Steps

### Step 1: Install Dependencies

Update the Python packages by running:

```bash
pip install -r requirements.txt
```

This will install:
- `mysql-connector-python` - MySQL database connector
- `Flask-Login` - Flask user session management
- `werkzeug` - Security utilities (password hashing)

### Step 2: Configure MySQL

Start your MySQL server:

**Windows:**
```bash
mysql -u root
```

**macOS/Linux:**
```bash
mysql -u root -p
```

You'll be prompted for a password if you set one during installation.

### Step 3: Set Environment Variables

Create environment variables for database connection:

**Windows (PowerShell):**
```powershell
$env:DB_HOST = "localhost"
$env:DB_USER = "root"
$env:DB_PASSWORD = "your_password"
$env:DB_NAME = "symptom_predictor"
$env:SECRET_KEY = "your-secret-key-change-in-production"
```

**macOS/Linux (Bash):**
```bash
export DB_HOST="localhost"
export DB_USER="root"
export DB_PASSWORD="your_password"
export DB_NAME="symptom_predictor"
export SECRET_KEY="your-secret-key-change-in-production"
```

> **Note:** If you didn't set a password during MySQL installation, leave `DB_PASSWORD` empty.

### Step 4: Initialize Database

Run the initialization script to create the database and tables:

```bash
python init_db.py
```

You should see:
```
Initializing database...
Database initialization completed successfully!
```

### Step 5: Run the Application

Start the Flask application:

```bash
python -m src.app
```

The application will be available at `http://localhost:8000`

## Features

### Authentication System

#### Login/Sign Up Page (`/auth`)
- **Sign Up**: Create new account with username, email, and password
- **Login**: Access existing account with username and password
- Forms toggle between login and signup views
- Client-side validation for password requirements

#### Security
- Passwords are hashed using `werkzeug.security.generate_password_hash`
- User sessions managed by Flask-Login
- Protected routes require login (e.g., `/dashboard`, `/settings`)

### User Features

#### Dashboard (`/dashboard`)
- Welcome message with username
- Quick access to predictor and other features
- Account information display
- Personalized experience for logged-in users

#### Settings (`/settings`)
- View account information
- Change password option
- Logout functionality

#### Navigation
- Dynamic navbar showing login/signup button for guests
- User menu dropdown for authenticated users
- Quick access to dashboard and settings

## Database Schema

### Users Table
```sql
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

## API Endpoints

### Authentication Endpoints

#### Sign Up
- **Endpoint**: `POST /api/signup`
- **Body**: 
  ```json
  {
    "username": "string",
    "email": "string",
    "password": "string"
  }
  ```
- **Response**:
  ```json
  {
    "success": true/false,
    "message": "string"
  }
  ```

#### Login
- **Endpoint**: `POST /api/login`
- **Body**:
  ```json
  {
    "username": "string",
    "password": "string"
  }
  ```
- **Response**:
  ```json
  {
    "success": true/false,
    "message": "string"
  }
  ```

#### Logout
- **Endpoint**: `GET /logout`
- **Requires**: User authentication
- **Redirects to**: Home page

## Troubleshooting

### Error: "Access denied for user 'root'@'localhost'"
- Check MySQL is running
- Verify username and password are correct
- Ensure environment variables are set

### Error: "Unknown database 'symptom_predictor'"
- Run `python init_db.py` to create database

### Error: "No module named 'mysql.connector'"
- Run `pip install mysql-connector-python`

### Password validation errors
- Passwords must be at least 6 characters
- Passwords must match during signup
- Use strong passwords (mix of letters, numbers, special characters)

## Security Notes

⚠️ **Important for Production:**

1. Change `SECRET_KEY` in environment to a random string:
   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

2. Use environment variables from `.env` file (not committed to git)

3. Use HTTPS in production

4. Set up proper database user with limited permissions

5. Implement password complexity requirements

6. Add rate limiting to login/signup endpoints

7. Implement email verification

## Advanced Configuration

### Custom Database Host
If MySQL is running on a different host:
```bash
export DB_HOST="192.168.1.100"
```

### Custom Port
If MySQL is on a non-standard port, modify `src/database.py`:
```python
self.connection = mysql.connector.connect(
    host=self.host,
    user=self.user,
    password=self.password,
    database=self.database,
    port=3306  # Change this
)
```

### Connection Pooling
For production, consider adding connection pooling in `src/database.py`

## Next Steps

1. Test the login/signup functionality
2. Create user accounts
3. Access the predictor while logged in
4. Customize user dashboard and features

## Support

For issues with:
- **MySQL**: Check MySQL documentation
- **Flask-Login**: Check Flask-Login documentation
- **Application**: Review logs in console for error messages

---

Created for Symptom-based Disease Prediction System
