from pymongo import MongoClient
import streamlit as st
import urllib.parse
from bson.objectid import ObjectId
import sys  # Import the sys module

def init_connection():
    """
    Initializes the MongoDB connection using credentials from Streamlit secrets.
    Handles connection errors and provides detailed debugging.
    """
    try:
        # 1. Debug: Print the raw values *before* encoding, with extra checks
        if 'mongo' in st.secrets:
            username = st.secrets["mongo"]["username"]
            password = st.secrets["mongo"]["password"]
            cluster_url = st.secrets["mongo"]["cluster"]
            db_name = st.secrets["mongo"]["db"]

            st.write(f"Raw username from secrets: {username!r}, type: {type(username)}")
            st.write(f"Raw password from secrets: {password!r}, type: {type(password)}")

            # 2.  Check for pre-encoding (Advanced Debugging)
            if any(char in username for char in "%@:/" ) or any(char in password for char in "%@:/"):
                st.error("ERROR: Username or password appears to be ALREADY encoded before quote_plus!")
                st.stop() # Stop execution to prevent further errors

            # Encode the username and password using urllib.parse.quote_plus
            username_encoded = urllib.parse.quote_plus(username)
            password_encoded = urllib.parse.quote_plus(password)

            # 3. Debug: Print the *encoded* values
            st.write(f"Encoded username: {username_encoded!r}, type: {type(username_encoded)}")
            st.write(f"Encoded password: {password_encoded!r}, type: {type(password_encoded)}")

            # 4. Debug: Print the connection string that will be used.
            connection_string = f"mongodb+srv://{username_encoded}:{password_encoded}@{cluster_url}/{db_name}?retryWrites=true&w=majority"
            st.write(f"Connection String: {connection_string}")

            # 5. Debug:  Check Python Version and Encoding
            st.write(f"Python Version: {sys.version}")
            st.write(f"Python Encoding: {sys.getdefaultencoding()}")

            # Connect to MongoDB
            client = MongoClient(connection_string)

            # Test connection with a ping command
            try:
                client.admin.command('ping')
                st.success("Connected to MongoDB Atlas successfully!")
                return client
            except Exception as ping_err:
                st.error(f"Ping failed: {ping_err}")
                return None

        else:
            st.error("MongoDB credentials not found in secrets.  Please ensure they are defined in your Streamlit secrets.toml file.")
            return None
    except Exception as e:
        st.error(f"Could not connect to MongoDB Atlas: {e}")
        import traceback
        st.error(traceback.format_exc())
        return None

def init_database():
    """
    Initializes the database connection and returns the database object.
    Handles the case where the client is None (connection failed).
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

# ---  The rest of your code (get_user, register_user, etc.) remains the same ---
# ---  No changes needed below this line in this code block ---
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
                "created_at": datetime.now(),
                "last_login": None
            }
            result = db.users.insert_one(user_data) # capture the result
            return True, "Registration successful"
        except Exception as e:
            return False, str(e)
    return False, "Database connection failed"

def create_seller_listing(listing_data):
    """Creates a new seller listing in the database."""
    db = init_database()
    if db:
        try:
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
            result = collection.update_one( # Capture the result.
                {"_id": ObjectId(listing_id)},  # Use ObjectId for _id
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
            result = collection.delete_one({"_id": ObjectId(listing_id)}) # Capture result
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
            user = db.users.find_one({"_id": ObjectId(user_id)})
            if user and 'security_answer' in user:
                return bcrypt.checkpw(answer.encode('utf-8'), user['security_answer'])
            return False
        except Exception:
            return False
    return False
