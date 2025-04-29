import os
from dotenv import load_dotenv
import secrets
import base64

# Load environment variables
load_dotenv()

def generate_secret_key():
    """Generate a secure random secret key"""
    return base64.b64encode(secrets.token_bytes(32)).decode('utf-8')

# Get JWT secret from environment variable or generate a new one
JWT_SECRET = os.getenv('JWT_SECRET')
if not JWT_SECRET:
    JWT_SECRET = generate_secret_key()
    print("Generated new JWT_SECRET. Add this to your .env file:")
    print(f"JWT_SECRET={JWT_SECRET}")

# Other configuration settings
JWT_EXPIRATION_DAYS = 30