# import mysql.connector
# from mysql.connector import Error
# import os
# from dotenv import load_dotenv
# import bcrypt

# # Load environment variables
# load_dotenv()

# def get_database_connection():
#     try:
#         connection = mysql.connector.connect(
#             host=os.getenv('DB_HOST'),
#             user=os.getenv('DB_USER'),
#             password=os.getenv('DB_PASSWORD'),
#             database=os.getenv('DB_NAME')
#         )
#         return connection
#     except Error as e:
#         print(f"Error connecting to MySQL: {e}")
#         return None

# def init_database():
#     connection = get_database_connection()
#     if connection:
#         try:
#             cursor = connection.cursor()
            
#             # Create users table
#             cursor.execute("""
#                 CREATE TABLE IF NOT EXISTS users (
#                     id INT AUTO_INCREMENT PRIMARY KEY,
#                     username VARCHAR(50) UNIQUE NOT NULL,
#                     password VARCHAR(255) NOT NULL,
#                     email VARCHAR(100) UNIQUE NOT NULL,
#                     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#                 )
#             """)
            
#             connection.commit()
#             print("Database initialized successfully")
#         except Error as e:
#             print(f"Error initializing database: {e}")
#         finally:
#             if connection.is_connected():
#                 cursor.close()
#                 connection.close()

# def create_user(username, password, email):
#     connection = get_database_connection()
#     if connection:
#         try:
#             cursor = connection.cursor()
            
#             # Hash the password
#             hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            
#             # Insert new user
#             cursor.execute("""
#                 INSERT INTO users (username, password, email)
#                 VALUES (%s, %s, %s)
#             """, (username, hashed_password, email))
            
#             connection.commit()
#             return True
#         except Error as e:
#             print(f"Error creating user: {e}")
#             return False
#         finally:
#             if connection.is_connected():
#                 cursor.close()
#                 connection.close()

# def verify_user(username, password):
#     connection = get_database_connection()
#     if connection:
#         try:
#             cursor = connection.cursor(dictionary=True)
            
#             # Get user by username
#             cursor.execute("""
#                 SELECT * FROM users
#                 WHERE username = %s
#             """, (username,))
            
#             user = cursor.fetchone()
            
#             if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
#                 return user
#             return None
#         except Error as e:
#             print(f"Error verifying user: {e}")
#             return None
#         finally:
#             if connection.is_connected():
#                 cursor.close()
#                 connection.close()

# # Initialize database when module is imported
# init_database() 


# database.py
# database.py
import mysql.connector
import hashlib
import uuid
import bcrypt
import secrets
from mysql.connector import Error
from datetime import datetime, timedelta

def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",  # Remplacez par votre nom d'utilisateur MySQL
            password="",  # Remplacez par votre mot de passe MySQL
            database="medical_report_app"  # Remplacez par le nom de votre base de données
        )
        
        # Create tables if they don't exist
        cursor = conn.cursor(dictionary=True)
        
        # Users table with new fields
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(255) NOT NULL UNIQUE,
            email VARCHAR(255) NOT NULL UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            email_verified BOOLEAN DEFAULT FALSE,
            verification_token VARCHAR(255),
            verification_token_expires DATETIME,
            reset_token VARCHAR(255),
            reset_token_expires DATETIME,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # User profiles table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_profiles (
            user_id INT PRIMARY KEY,
            first_name VARCHAR(255),
            last_name VARCHAR(255),
            dob VARCHAR(255),
            patient_id VARCHAR(255),
            gender VARCHAR(50),
            phone VARCHAR(255),
            medical_history TEXT,
            medications TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')
        
        # Reports table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS reports (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT,
            report_title VARCHAR(255),
            report_content TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            language VARCHAR(50),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')
        
        conn.commit()
        return conn
    except Error as e:
        print(f"Error connecting to MySQL database: {e}")
        return None

def create_user(username, password, email):
    try:
        conn = get_db_connection()
        if not conn:
            return False
            
        cursor = conn.cursor(dictionary=True)
        
        # Check if username or email already exists
        cursor.execute('SELECT * FROM users WHERE username = %s OR email = %s', (username, email))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return False
        
        # Generate verification token
        verification_token = secrets.token_urlsafe(32)
        verification_expires = datetime.utcnow() + timedelta(hours=24)
        
        # Hash the password using bcrypt
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # Insert the new user
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, verification_token, verification_token_expires)
            VALUES (%s, %s, %s, %s, %s)
        ''', (username, email, password_hash, verification_token, verification_expires))
        
        # Get the user id
        user_id = cursor.lastrowid
        
        # Create an empty profile for the user
        cursor.execute('INSERT INTO user_profiles (user_id) VALUES (%s)', (user_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        return True
        
    except Error as e:
        print(f"Error creating user: {e}")
        return False

def verify_user_by_email(email, password):
    try:
        conn = get_db_connection()
        if not conn:
            return None
            
        cursor = conn.cursor(dictionary=True)
        
        # Get user by email
        cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
        user = cursor.fetchone()
        
        if not user:
            cursor.close()
            conn.close()
            return None
            
        # Verify password using bcrypt
        if not bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
            cursor.close()
            conn.close()
            return None
            
        cursor.close()
        conn.close()
        return user
        
    except Error as e:
        print(f"Error verifying user: {e}")
        return None

def verify_email(token):
    try:
        conn = get_db_connection()
        if not conn:
            return False
            
        cursor = conn.cursor(dictionary=True)
        
        # Find user with matching token
        cursor.execute('''
            SELECT * FROM users 
            WHERE verification_token = %s 
            AND verification_token_expires > %s
        ''', (token, datetime.utcnow()))
        
        user = cursor.fetchone()
        
        if not user:
            cursor.close()
            conn.close()
            return False
            
        # Update user as verified
        cursor.execute('''
            UPDATE users 
            SET email_verified = TRUE,
                verification_token = NULL,
                verification_token_expires = NULL
            WHERE id = %s
        ''', (user['id'],))
        
        conn.commit()
        cursor.close()
        conn.close()
        return True
        
    except Error as e:
        print(f"Error verifying email: {e}")
        return False

def request_password_reset(email):
    try:
        conn = get_db_connection()
        if not conn:
            return False
            
        cursor = conn.cursor(dictionary=True)
        
        # Check if user exists
        cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
        user = cursor.fetchone()
        
        if not user:
            cursor.close()
            conn.close()
            return False
            
        # Generate reset token
        reset_token = secrets.token_urlsafe(32)
        reset_expires = datetime.utcnow() + timedelta(hours=1)
        
        # Update user with reset token
        cursor.execute('''
            UPDATE users 
            SET reset_token = %s,
                reset_token_expires = %s
            WHERE id = %s
        ''', (reset_token, reset_expires, user['id']))
        
        conn.commit()
        cursor.close()
        conn.close()
        return reset_token
        
    except Error as e:
        print(f"Error requesting password reset: {e}")
        return False

def reset_password(token, new_password):
    try:
        conn = get_db_connection()
        if not conn:
            return False
            
        cursor = conn.cursor(dictionary=True)
        
        # Find user with matching token
        cursor.execute('''
            SELECT * FROM users 
            WHERE reset_token = %s 
            AND reset_token_expires > %s
        ''', (token, datetime.utcnow()))
        
        user = cursor.fetchone()
        
        if not user:
            cursor.close()
            conn.close()
            return False
            
        # Hash new password
        password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
        
        # Update password and clear reset token
        cursor.execute('''
            UPDATE users 
            SET password_hash = %s,
                reset_token = NULL,
                reset_token_expires = NULL
            WHERE id = %s
        ''', (password_hash, user['id']))
        
        conn.commit()
        cursor.close()
        conn.close()
        return True
        
    except Error as e:
        print(f"Error resetting password: {e}")
        return False

def get_user_profile(email):
    try:
        conn = get_db_connection()
        if not conn:
            return {}
            
        cursor = conn.cursor(dictionary=True)
        
        # Get user ID
        cursor.execute('SELECT id, username FROM users WHERE email = %s', (email,))
        user = cursor.fetchone()
        
        if not user:
            cursor.close()
            conn.close()
            return {}
        
        user_id = user['id']
        username = user['username']
        
        # Get profile data
        cursor.execute('SELECT * FROM user_profiles WHERE user_id = %s', (user_id,))
        profile = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if profile:
            # Add username to profile dict
            profile['username'] = username
            return profile
        else:
            return {'username': username}
        
    except Error as e:
        print(f"Error getting user profile: {e}")
        return {}

def update_user_profile(email, profile_data):
    try:
        conn = get_db_connection()
        if not conn:
            return False
            
        cursor = conn.cursor(dictionary=True)
        
        # Get user ID
        cursor.execute('SELECT id FROM users WHERE email = %s', (email,))
        user = cursor.fetchone()
        
        if not user:
            cursor.close()
            conn.close()
            return False
        
        user_id = user['id']
        
        # Check if profile exists
        cursor.execute('SELECT 1 FROM user_profiles WHERE user_id = %s', (user_id,))
        profile_exists = cursor.fetchone()
        
        if profile_exists:
            # Update existing profile
            query = '''
            UPDATE user_profiles SET 
                first_name = %s,
                last_name = %s,
                dob = %s,
                patient_id = %s,
                gender = %s,
                phone = %s,
                medical_history = %s,
                medications = %s
            WHERE user_id = %s
            '''
            cursor.execute(query, (
                profile_data.get('first_name', ''),
                profile_data.get('last_name', ''),
                profile_data.get('dob', ''),
                profile_data.get('patient_id', ''),
                profile_data.get('gender', ''),
                profile_data.get('phone', ''),
                profile_data.get('medical_history', ''),
                profile_data.get('medications', ''),
                user_id
            ))
        else:
            # Create new profile
            query = '''
            INSERT INTO user_profiles (
                user_id, first_name, last_name, dob, patient_id, gender, phone, medical_history, medications
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            '''
            cursor.execute(query, (
                user_id,
                profile_data.get('first_name', ''),
                profile_data.get('last_name', ''),
                profile_data.get('dob', ''),
                profile_data.get('patient_id', ''),
                profile_data.get('gender', ''),
                profile_data.get('phone', ''),
                profile_data.get('medical_history', ''),
                profile_data.get('medications', '')
            ))
        
        conn.commit()
        cursor.close()
        conn.close()
        return True
        
    except Error as e:
        print(f"Error updating user profile: {e}")
        return False

def save_report(user_email, report_title, report_content, language='en'):
    try:
        conn = get_db_connection()
        if not conn:
            return False
            
        cursor = conn.cursor(dictionary=True)
        
        # Get user ID
        cursor.execute('SELECT id FROM users WHERE email = %s', (user_email,))
        user = cursor.fetchone()
        
        if not user:
            cursor.close()
            conn.close()
            return False
        
        user_id = user['id']
        
        # Save report
        cursor.execute(
            'INSERT INTO reports (user_id, report_title, report_content, language) VALUES (%s, %s, %s, %s)',
            (user_id, report_title, report_content, language)
        )
        
        conn.commit()
        cursor.close()
        conn.close()
        return True
    
    except Error as e:
        print(f"Error saving report: {e}")
        return False

def get_user_reports(user_email):
    try:
        conn = get_db_connection()
        if not conn:
            return []
            
        cursor = conn.cursor(dictionary=True)
        
        # Get user ID
        cursor.execute('SELECT id FROM users WHERE email = %s', (user_email,))
        user = cursor.fetchone()
        
        if not user:
            cursor.close()
            conn.close()
            return []
        
        user_id = user['id']
        
        # Get reports
        cursor.execute('''
            SELECT id, report_title, created_at, language 
            FROM reports 
            WHERE user_id = %s 
            ORDER BY created_at DESC
        ''', (user_id,))
        
        reports = cursor.fetchall()
        
        cursor.close()
        conn.close()
        return reports
    
    except Error as e:
        print(f"Error getting user reports: {e}")
        return []