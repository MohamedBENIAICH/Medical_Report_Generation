from google.oauth2 import id_token
from google.auth.transport import requests
import os

def handle_google_signin(token):
    try:
        # Verify the token
        idinfo = id_token.verify_oauth2_token(token, requests.Request())
        
        # Get user info from the token
        email = idinfo['email']
        name = idinfo.get('name', email.split('@')[0])
        
        # Here you would typically:
        # 1. Check if user exists in your database
        # 2. Create user if they don't exist
        # 3. Set up session
        
        return True
    except Exception as e:
        print(f"Error verifying Google token: {e}")
        return False 