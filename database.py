from pymongo import MongoClient
import streamlit as st
from datetime import datetime
import bcrypt
import os
from bson.objectid import ObjectId

def init_connection():
    try:
        # First try to get connection string from Streamlit secrets
        if 'mongo' in st.secrets:
            mongo_uri = st.secrets['mongo']['uri']
        # Then try environment variables
        else:
            mongo_uri = os.getenv('MONGO_URI')
        
        # If both fail, show a helpful error
        if not mongo_uri:
            st.error("MongoDB connection string not found. Please set it in Streamlit secrets or as MONGO_URI environment variable.")
            return None
            
        # Connect with the URI
        client = MongoClient(mongo_uri)
        # Verify connection works
        client.admin.command('ping')
        return client
    except Exception as e:
        st.error(f"Could not connect to MongoDB: {e}")
        return None

def init_database():
    client = init_connection()
    if client is not None:
        # Get database name from secrets or use default
        if 'mongo' in st.secrets and 'database' in st.secrets['mongo']:
            db_name = st.secrets['mongo']['database']
        else:
            db_name = os.getenv('MONGO_DB', 'waste_exchange')
        return client[db_name]
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
                {"_id": ObjectId(listing_id) if isinstance(listing_id, str) else listing_id},
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
            collection.delete_one({"_id": ObjectId(listing_id) if isinstance(listing_id, str) else listing_id})
            return True, "Deleted successfully"
        except Exception as e:
            return False, str(e)
    return False, "Database connection failed"

def update_user_password(user_id, new_password_hash):
    """Updates a user's password in the database"""
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
