from pymongo import MongoClient
import streamlit as st
import urllib.parse
from bson.objectid import ObjectId
import sys
import ssl
from datetime import datetime  # Add this import for datetime

def init_connection():
    """
    Initializes the MongoDB connection using credentials from Streamlit secrets.
    Uses custom SSL context which was proven to work.
    """
    try:
        if 'mongo' in st.secrets:
            username = st.secrets["mongo"]["username"]
            password = st.secrets["mongo"]["password"]
            cluster_url = st.secrets["mongo"]["cluster"]
            db_name = st.secrets["mongo"]["db"]

            # Debug info
            
            
            # Encode credentials
            username_encoded = urllib.parse.quote_plus(username)
            password_encoded = urllib.parse.quote_plus(password)
            
            
            
            # Extract the base domain from the cluster URL for direct connection attempts
            base_domain = ".".join(cluster_url.split(".")[1:]) if len(cluster_url.split(".")) > 2 else cluster_url
            
            # Use the connection method that worked: custom SSL context with direct connection
            try:
               
                
                # Create a custom SSL context with lower security requirements
                ctx = ssl.SSLContext(ssl.PROTOCOL_TLS)
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                
                uri = f"mongodb://{username_encoded}:{password_encoded}@ac-e9filvk-shard-00-00.{base_domain}:27017,ac-e9filvk-shard-00-01.{base_domain}:27017,ac-e9filvk-shard-00-02.{base_domain}:27017/{db_name}?authSource=admin"
                
                client = MongoClient(
                    uri,
                    ssl=True, 
                    ssl_cert_reqs=ssl.CERT_NONE,
                    serverSelectionTimeoutMS=5000
                )
                
                # Test the connection
                client.admin.command('ping')
                
                return client
                
            except Exception as e:
                st.error(f"Connection failed: {str(e)}")
                
                # Provide troubleshooting guidance
                st.error("""
                Troubleshooting advice:
                1. Check if your IP address is whitelisted in MongoDB Atlas Network Access
                2. Verify your username and password in the secrets.toml file
                3. Ensure there are no network restrictions blocking outbound connections to MongoDB Atlas
                4. Check if your MongoDB Atlas cluster is active and running
                """)
                
                return None
                
        else:
            st.error("MongoDB credentials not found in secrets. Please ensure they are defined in your Streamlit secrets.toml file.")
            return None
            
    except Exception as e:
        st.error(f"Could not connect to MongoDB Atlas: {e}")
        import traceback
        st.error(traceback.format_exc())
        return None

def init_database():
    """
    Initializes the database connection and returns the database object.
    """
    client = init_connection()
    if client:
        try:
            db_name = st.secrets["mongo"]["db"]
            db = client[db_name]
            return db
        except Exception as e:
            st.error(f"Error accessing database: {e}")
            return None
    else:
        return None

# --- Database operation functions ---

def get_user(email):
    """Retrieves a user document from the database based on email."""
    db = init_database()
    if db:
        return db.users.find_one({"email": email})
    return None

def register_user(username, email, password_hash):
    """Registers a new user in the database."""
    db = init_database()
    if db:
        try:
            user_data = {
                "username": username,
                "email": email,
                "password": password_hash,
                "created_at": datetime.now(),  # Uses the imported datetime
                "last_login": None
            }
            result = db.users.insert_one(user_data)
            return True, "Registration successful"
        except Exception as e:
            return False, str(e)
    return False, "Database connection failed"

def create_seller_listing(listing_data):
    """Creates a new seller listing in the database."""
    db = init_database()
    if db:
        try:
            # Make sure the listing data has a timestamp
            if "created_at" not in listing_data:
                listing_data["created_at"] = datetime.now()
                
            result = db.seller_listings.insert_one(listing_data)
            return True, str(result.inserted_id)
        except Exception as e:
            return False, str(e)
    return False, "Database connection failed"

def get_seller_listings(query=None):
    """Retrieves seller listings from the database, optionally filtered by a query."""
    db = init_database()
    if db:
        if query is None:
            query = {"status": "Active"}
        return list(db.seller_listings.find(query).sort("created_at", -1))
    return []

def create_buyer_request(request_data):
    """Creates a new buyer request in the database."""
    db = init_database()
    if db:
        try:
            # Make sure the request data has a timestamp
            if "created_at" not in request_data:
                request_data["created_at"] = datetime.now()
                
            result = db.buyer_requests.insert_one(request_data)
            return True, str(result.inserted_id)
        except Exception as e:
            return False, str(e)
    return False, "Database connection failed"

def get_buyer_requests(query=None):
    """Retrieves buyer requests from the database, optionally filtered by a query."""
    db = init_database()
    if db:
        if query is None:
            query = {"status": "Active"}
        return list(db.buyer_requests.find(query).sort("created_at", -1))
    return []

def update_listing_status(listing_id, collection_name, new_status):
    """Updates the status of a listing (seller or buyer) in the database."""
    db = init_database()
    if db:
        try:
            collection = db[collection_name]
            result = collection.update_one(
                {"_id": ObjectId(listing_id)},
                {"$set": {"status": new_status}}
            )
            if result.modified_count > 0:
                return True, "Updated successfully"
            else:
                return False, "Listing not found or status not changed"
        except Exception as e:
            return False, str(e)
    return False, "Database connection failed"

def delete_listing(listing_id, collection_name):
    """Deletes a listing (seller or buyer) from the database."""
    db = init_database()
    if db:
        try:
            collection = db[collection_name]
            result = collection.delete_one({"_id": ObjectId(listing_id)})
            if result.deleted_count > 0:
                return True, "Deleted successfully"
            else:
                return False, "Listing not found"
        except Exception as e:
            return False, str(e)
    return False, "Database connection failed"

def update_user_password(user_id, new_password_hash):
    """Updates a user's password in the database"""
    db = init_database()
    if db:
        try:
            import bcrypt  # Import here to avoid missing import
            
            # Make sure the password is properly hashed before storing
            if not isinstance(new_password_hash, bytes):
                new_password_hash = bcrypt.hashpw(new_password_hash.encode('utf-8'), bcrypt.gensalt())

            result = db.users.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {"password": new_password_hash}}
            )
            if result.modified_count > 0:
                return True, "Password updated successfully"
            else:
                return False, "User not found or password not changed"

        except Exception as e:
            return False, str(e)
    return False, "Database connection failed"

def add_security_question(user_id, question, answer):
    """Adds a security question and answer to user profile"""
    db = init_database()
    if db:
        try:
            import bcrypt  # Import here to avoid missing import
            
            # Hash the security answer for security
            answer_hash = bcrypt.hashpw(answer.encode('utf-8'), bcrypt.gensalt())
            result = db.users.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {
                    "security_question": question,
                    "security_answer": answer_hash
                }}
            )
            if result.modified_count > 0:
                return True, "Security question added"
            else:
                return False, "User not found or question not added"
        except Exception as e:
            return False, str(e)
    return False, "Database connection failed"

def verify_security_question(user_id, answer):
    """Verifies if the provided answer matches the stored security answer"""
    db = init_database()
    if db:
        try:
            import bcrypt  # Import here to avoid missing import
            
            user = db.users.find_one({"_id": ObjectId(user_id)})
            if user and 'security_answer' in user:
                return bcrypt.checkpw(answer.encode('utf-8'), user['security_answer'])
            return False
        except Exception:
            return False
    return False
