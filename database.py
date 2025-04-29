from pymongo import MongoClient
import streamlit as st
from datetime import datetime
import bcrypt
import os
import ssl

def init_connection():
    try:
        # Check for MongoDB URI in Streamlit secrets first
        if "mongo" in st.secrets:
            mongo_uri = st.secrets["mongo"]["uri"]
        # Fall back to environment variable
        else:
            mongo_uri = os.environ.get("MONGODB_URI")
            
        if not mongo_uri:
            st.error("MongoDB connection string not found in secrets or environment variables")
            return None
        
        # Important: Make sure the URI specifies the database
        if "waste_exchange" not in mongo_uri and "?" in mongo_uri:
            # Insert database name before query parameters
            mongo_uri = mongo_uri.replace("/?", "/waste_exchange?")
            
        # Create SSL context with appropriate settings
        ssl_context = ssl.create_default_context()
        
        # Connect with SSL settings
        client = MongoClient(
            mongo_uri, 
            serverSelectionTimeoutMS=10000,
            ssl=True,
            ssl_cert_reqs=ssl.CERT_NONE,  # Bypass strict certificate validation
            connectTimeoutMS=30000,
            socketTimeoutMS=30000,
            retryWrites=True,
            w="majority"  # Ensure writes are acknowledged by majority of replicas
        )
        
        # Force a connection to verify it works
        client.admin.command('ping')
        st.success("Connected to MongoDB successfully")
        
        return client
    except Exception as e:
        st.error(f"Could not connect to MongoDB: {e}")
        st.info("Please check your connection string and network settings")
        return None

def init_database():
    client = init_connection()
    if client is not None:
        return client['waste_exchange']
    return None
def get_user(email):
    db = init_database()
    if db is not None:
        return db.users.find_one({"email": email})
    return None

def register_user(username, email, password_hash):
    db = init_database()
    if db is not None:
        try:
            db.users.insert_one({
                "username": username,
                "email": email,
                "password": password_hash,
                "created_at": datetime.now(),
                
                "last_login": None
            })
            return True, "Registration successful"
        except Exception as e:
            return False, str(e)
    return False, "Database connection failed"

def create_seller_listing(listing_data):
    db = init_database()
    if db is not None:
        try:
            result = db.seller_listings.insert_one(listing_data)
            return True, str(result.inserted_id)
        except Exception as e:
            return False, str(e)
    return False, "Database connection failed"

def get_seller_listings(query=None):
    db = init_database()
    if db is not None:
        if query is None:
            query = {"status": "Active"}
        return list(db.seller_listings.find(query).sort("created_at", -1))
    return []

def create_buyer_request(request_data):
    db = init_database()
    if db is not None:
        try:
            result = db.buyer_requests.insert_one(request_data)
            return True, str(result.inserted_id)
        except Exception as e:
            return False, str(e)
    return False, "Database connection failed"

def get_buyer_requests(query=None):
    db = init_database()
    if db is not None:
        if query is None:
            query = {"status": "Active"}
        return list(db.buyer_requests.find(query).sort("created_at", -1))
    return []

def update_listing_status(listing_id, collection_name, new_status):
    db = init_database()
    if db is not None:
        try:
            collection = db[collection_name]
            collection.update_one(
                {"_id": listing_id},
                {"$set": {"status": new_status}}
            )
            return True, "Updated successfully"
        except Exception as e:
            return False, str(e)
    return False, "Database connection failed"

def delete_listing(listing_id, collection_name):
    db = init_database()
    if db is not None:
        try:
            collection = db[collection_name]
            collection.delete_one({"_id": listing_id})
            return True, "Deleted successfully"
        except Exception as e:
            return False, str(e)
    return False, "Database connection failed"

def update_user_password(user_id, new_password_hash):
    """Updates a user's password in the database"""
    from bson.objectid import ObjectId
    db = init_database()
    if db is not None:
        try:
            # Make sure the password is properly hashed before storing
            if not isinstance(new_password_hash, bytes):
                new_password_hash = bcrypt.hashpw(new_password_hash.encode('utf-8'), bcrypt.gensalt())
            
            db.users.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {"password": new_password_hash}}
            )
            return True, "Password updated successfully"
        except Exception as e:
            return False, str(e)
    return False, "Database connection failed"

def add_security_question(user_id, question, answer):
    """Adds a security question and answer to user profile"""
    from bson.objectid import ObjectId
    db = init_database()
    if db is not None:
        try:
            # Hash the security answer for security
            answer_hash = bcrypt.hashpw(answer.encode('utf-8'), bcrypt.gensalt())
            db.users.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {
                    "security_question": question,
                    "security_answer": answer_hash
                }}
            )
            return True, "Security question added"
        except Exception as e:
            return False, str(e)
    return False, "Database connection failed"

def verify_security_question(user_id, answer):
    """Verifies if the provided answer matches the stored security answer"""
    from bson.objectid import ObjectId
    db = init_database()
    if db is not None:
        try:
            user = db.users.find_one({"_id": ObjectId(user_id)})
            if user and 'security_answer' in user:
                return bcrypt.checkpw(answer.encode('utf-8'), user['security_answer'])
            return False
        except Exception:
            return False
    return False
