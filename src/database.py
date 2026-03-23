import mysql.connector
from mysql.connector import Error
from werkzeug.security import generate_password_hash, check_password_hash
import os

class Database:
    def __init__(self):
        self.host = os.environ.get('DB_HOST', 'localhost')
        self.user = os.environ.get('DB_USER', 'root')
        self.password = os.environ.get('DB_PASSWORD', '')
        self.database = os.environ.get('DB_NAME', 'disease_recognition')
        self.connection = None
    
    def connect(self):
        """Establish connection to MySQL database"""
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database
            )
            return self.connection
        except Error as e:
            print(f"Error while connecting to MySQL: {e}")
            return None
    
    def disconnect(self):
        """Close database connection"""
        if self.connection and self.connection.is_connected():
            self.connection.close()

    def ensure_prediction_schema(self):
        """Add symptoms column to prediction_history when upgrading older databases."""
        try:
            connection = self.connect()
            if not connection:
                return
            cursor = connection.cursor()
            cursor.execute(
                "SHOW COLUMNS FROM prediction_history LIKE %s", ("symptoms",)
            )
            if not cursor.fetchone():
                cursor.execute(
                    "ALTER TABLE prediction_history ADD COLUMN symptoms TEXT NULL"
                )
                connection.commit()
            cursor.close()
            connection.close()
        except Exception as e:
            print(f"ensure_prediction_schema: {e}")

    def init_db(self):
        """Initialize database tables"""
        try:
            connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password
            )
            cursor = connection.cursor()
            
            # Create database if not exists
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.database}")
            connection.database = self.database
            
            # Create users table
            create_users_table = """
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(80) UNIQUE NOT NULL,
                email VARCHAR(120) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                role VARCHAR(20) DEFAULT 'user',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            cursor.execute(create_users_table)

            # Create diseases table
            create_diseases_table = """
CREATE TABLE IF NOT EXISTS diseases (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(120) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""
            cursor.execute(create_diseases_table)

            # Create prediction_history table
            create_history_table = """
CREATE TABLE IF NOT EXISTS prediction_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    report_id VARCHAR(64) NOT NULL,
    user_id INT,
    patient_name VARCHAR(120),
    predicted_disease VARCHAR(120),
    recommended_tests TEXT,
    symptoms TEXT,
    prediction_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
)
"""
            cursor.execute(create_history_table)
            try:
                cursor.execute(
                    "ALTER TABLE prediction_history ADD COLUMN symptoms TEXT NULL"
                )
                connection.commit()
            except Error as e:
                if "Duplicate column" not in str(e):
                    raise
            connection.commit()
            cursor.close()
            connection.close()
            print("Database initialized successfully")
        except Error as e:
            print(f"Error initializing database: {e}")

    def add_disease(self, name, description):
        try:
            connection = self.connect()
            if not connection:
                return False
            cursor = connection.cursor()
            insert_query = """
                INSERT INTO diseases (name, description) VALUES (%s, %s)
            """
            cursor.execute(insert_query, (name, description))
            connection.commit()
            cursor.close()
            connection.close()
            return True
        except Exception as e:
            print(f"Error adding disease: {e}")
            return False

    def get_all_diseases(self):
        try:
            connection = self.connect()
            if not connection:
                return []
            cursor = connection.cursor(dictionary=True)
            query = "SELECT * FROM diseases ORDER BY created_at DESC"
            cursor.execute(query)
            results = cursor.fetchall()
            cursor.close()
            connection.close()
            return results
        except Exception as e:
            print(f"Error fetching diseases: {e}")
            return []

            # Create prediction_history table
            create_history_table = """
            CREATE TABLE IF NOT EXISTS prediction_history (
                id INT AUTO_INCREMENT PRIMARY KEY,
                report_id VARCHAR(64) NOT NULL,
                user_id INT,
                patient_name VARCHAR(120),
                predicted_disease VARCHAR(120),
                recommended_tests TEXT,
                prediction_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            """
            cursor.execute(create_history_table)
            connection.commit()
            cursor.close()
            connection.close()
            print("Database initialized successfully")
        except Error as e:
            print(f"Error initializing database: {e}")

    def save_prediction(
        self,
        user_id,
        report_id,
        patient_name,
        predicted_disease,
        recommended_tests,
        symptoms=None,
    ):
        try:
            connection = self.connect()
            if not connection:
                return False
            cursor = connection.cursor()
            tests_str = ", ".join(recommended_tests) if recommended_tests else ""
            sym_str = ", ".join(symptoms) if symptoms else None
            insert_query = """
                INSERT INTO prediction_history (report_id, user_id, patient_name, predicted_disease, recommended_tests, symptoms)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(
                insert_query,
                (
                    report_id,
                    user_id,
                    patient_name,
                    predicted_disease,
                    tests_str,
                    sym_str,
                ),
            )
            connection.commit()
            cursor.close()
            connection.close()
            return True
        except Exception as e:
            print(f"Error saving prediction: {e}")
            return False

    def get_prediction_history(self, user_id):
        try:
            connection = self.connect()
            if not connection:
                return []
            cursor = connection.cursor(dictionary=True)
            query = """
                SELECT * FROM prediction_history WHERE user_id = %s ORDER BY prediction_date DESC
            """
            cursor.execute(query, (user_id,))
            results = cursor.fetchall()
            cursor.close()
            connection.close()
            return results
        except Exception as e:
            print(f"Error fetching prediction history: {e}")
            return []

    def get_prediction_by_report_id(self, report_id, user_id):
        try:
            connection = self.connect()
            if not connection:
                return None
            cursor = connection.cursor(dictionary=True)
            query = """
                SELECT * FROM prediction_history WHERE report_id = %s AND user_id = %s
            """
            cursor.execute(query, (report_id, user_id))
            result = cursor.fetchone()
            cursor.close()
            connection.close()
            return result
        except Exception as e:
            print(f"Error fetching prediction by report_id: {e}")
            return None
            print("Database initialized successfully")
        except Error as e:
            print(f"Error initializing database: {e}")
    
    def register_user(self, username, email, password, role='user'):
        """Register a new user"""
        try:
            connection = self.connect()
            if not connection:
                return {'success': False, 'message': 'Database connection failed'}
            
            cursor = connection.cursor()
            hashed_password = generate_password_hash(password)
            
            insert_query = "INSERT INTO users (username, email, password, role) VALUES (%s, %s, %s, %s)"
            cursor.execute(insert_query, (username, email, hashed_password, role))
            connection.commit()
            cursor.close()
            connection.close()
            
            return {'success': True, 'message': 'User registered successfully'}
        except Error as e:
            if 'Duplicate entry' in str(e):
                return {'success': False, 'message': 'Username or email already exists'}
            return {'success': False, 'message': f'Registration failed: {str(e)}'}
    
    def login_user(self, username, password):
        """Authenticate user"""
        try:
            connection = self.connect()
            if not connection:
                return {'success': False, 'message': 'Database connection failed'}
            
            cursor = connection.cursor(dictionary=True)
            query = "SELECT id, username, email, password, role FROM users WHERE username = %s"
            cursor.execute(query, (username,))
            user = cursor.fetchone()
            cursor.close()
            connection.close()
            
            if user and check_password_hash(user['password'], password):
                return {
                    'success': True,
                    'message': 'Login successful',
                    'user': {
                        'id': user['id'],
                        'username': user['username'],
                        'email': user['email'],
                        'role': user.get('role', 'user')
                    }
                }
            else:
                return {'success': False, 'message': 'Invalid username or password'}
        except Error as e:
            return {'success': False, 'message': f'Login failed: {str(e)}'}
    
    def get_user(self, username):
        """Get user by username"""
        try:
            connection = self.connect()
            if not connection:
                return None
            
            cursor = connection.cursor(dictionary=True)
            query = "SELECT id, username, email, role FROM users WHERE username = %s"
            cursor.execute(query, (username,))
            user = cursor.fetchone()
            cursor.close()
            connection.close()
            
            return user
        except Error as e:
            print(f"Error fetching user: {e}")
            return None
    
    def get_user_by_id(self, user_id):
        """Get user by ID"""
        try:
            connection = self.connect()
            if not connection:
                return None
            
            cursor = connection.cursor(dictionary=True)
            query = "SELECT id, username, email, role FROM users WHERE id = %s"
            cursor.execute(query, (user_id,))
            user = cursor.fetchone()
            cursor.close()
            connection.close()
            
            return user
        except Error as e:
            print(f"Error fetching user by ID: {e}")
            return None

# Create a global database instance
db = Database()
