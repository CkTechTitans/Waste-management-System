import pymongo
from datetime import datetime, timedelta
import secrets
import hashlib
from bson.objectid import ObjectId

import pymongo
from datetime import datetime, timedelta
import secrets
import hashlib
from bson.objectid import ObjectId
import os
import urllib.parse
import ssl
import streamlit as st

def connect_to_mongodb():
    """Connects to the MongoDB Atlas database.
    
    Handles both environment variable and Streamlit secrets configuration.
    """
    try:
        # First try to get connection info from environment variables
        connection_string = os.environ.get("MONGODB_URI")
        
        # If environment variable not found, try Streamlit secrets
        if not connection_string and 'mongo' in st.secrets:
            username = st.secrets["mongo"]["username"]
            password = st.secrets["mongo"]["password"]
            cluster_url = st.secrets["mongo"]["cluster"]
            db_name = st.secrets["mongo"]["db"]
            
            # Encode credentials
            username_encoded = urllib.parse.quote_plus(username)
            password_encoded = urllib.parse.quote_plus(password)
            
            # Extract base domain for direct connection
            base_domain = ".".join(cluster_url.split(".")[1:]) if len(cluster_url.split(".")) > 2 else cluster_url
            
            # Create connection URI for replica set connection
            connection_string = f"mongodb://{username_encoded}:{password_encoded}@ac-e9filvk-shard-00-00.{base_domain}:27017,ac-e9filvk-shard-00-01.{base_domain}:27017,ac-e9filvk-shard-00-02.{base_domain}:27017/{db_name}?authSource=admin"
            
            # Create a client with custom SSL settings
            client = pymongo.MongoClient(
                connection_string,
                ssl=True,
                ssl_cert_reqs=ssl.CERT_NONE,
                serverSelectionTimeoutMS=5000
            )
        
        # If no connection string from either source, try the standard format from user input
        elif not connection_string:
            print("MongoDB Atlas connection credentials not found.")
            print("Please provide your MongoDB Atlas connection details:")
            
            username = input("Username: ")
            password = input("Password: ")
            cluster_url = input("Cluster URL (example: cluster0.abc123.mongodb.net): ")
            db_name = input("Database name: ")
            
            # Encode credentials
            username_encoded = urllib.parse.quote_plus(username)
            password_encoded = urllib.parse.quote_plus(password)
            
            # Create connection URI - standard MongoDB Atlas format
            connection_string = f"mongodb+srv://{username_encoded}:{password_encoded}@{cluster_url}/{db_name}?retryWrites=true&w=majority"
            
            # Store it for future use
            os.environ["MONGODB_URI"] = connection_string
            
            # Create a standard client
            client = pymongo.MongoClient(connection_string)
        
        # If we have a connection string from environment variable
        else:
            # Create a standard client
            client = pymongo.MongoClient(connection_string)
        
        # Get database name
        if 'mongo' in st.secrets and "db" in st.secrets["mongo"]:
            db_name = st.secrets["mongo"]["db"]
        else:
            # Extract database name from connection string or default to waste_management
            db_name = connection_string.split("/")[-1].split("?")[0] or "waste_management"
        
        # Access your database
        db = client[db_name]
        
        # Verify the connection works
        client.admin.command('ping')
        print("Successfully connected to MongoDB Atlas!")
        
        return db
    
    except pymongo.errors.ConnectionFailure as e:
        print(f"Could not connect to MongoDB Atlas: {e}")
        if 'streamlit' in sys.modules:
            st.error(f"Could not connect to MongoDB Atlas: {e}")
            st.error("""
            Troubleshooting advice:
            1. Check if your IP address is whitelisted in MongoDB Atlas Network Access
            2. Verify your username and password
            3. Ensure there are no network restrictions blocking outbound connections to MongoDB Atlas
            4. Check if your MongoDB Atlas cluster is active and running
            """)
        return None
    
    except Exception as e:
        print(f"Error connecting to MongoDB Atlas: {e}")
        if 'streamlit' in sys.modules:
            st.error(f"Error connecting to MongoDB Atlas: {e}")
            import traceback
            st.error(traceback.format_exc())
        return None

# The rest of your functions remain the same, just replace the original connect_to_mongodb function
# with this improved version that works with MongoDB Atlas
def initialize_admin_accounts():
    """Initializes the default admin account if none exist."""
    db = connect_to_mongodb()
    if db is None:
        return

    admin_users = db["admin_users"]
    if admin_users.count_documents({}) == 0:
        salt = secrets.token_hex(16)
        hashed_password = hashlib.sha256((salt + "admin1234").encode()).hexdigest()
        
        # Create admin with both field types for maximum compatibility
        admin_users.insert_one({
            "username": "admin", 
            "password": hashed_password,
            "hashed_password": hashed_password,
            "salt": salt
        })
        print("Default admin account created. Please change the password immediately.")

def verify_admin(username, password):
    """Verifies the admin username and password."""
    try:
        db = connect_to_mongodb()
        if db is None:
            print("Database connection error in verify_admin")
            return False

        admin_users = db["admin_users"]
        admin = admin_users.find_one({"username": username})

        if not admin:
            
            return False

        if "salt" not in admin:
            
            return False

        # Possible password fields
        hashed_fields = ["hashed_password", "password", "password_hash"]
        salt = admin["salt"]
        hashed_input = hashlib.sha256((password + admin["salt"]).encode()).hexdigest()


       

        for field in hashed_fields:
            if field in admin:
                
                if hashed_input == admin[field]:
                    
                    return True

        print("Password verification failed")
        return False

    except Exception as e:
        print(f"Error in verify_admin: {str(e)}")
        return False



def change_admin_password(username, current_password, new_password):
    """Changes the admin password."""
    try:
        db = connect_to_mongodb()
        if db is None:
            return False, "Database connection error"

        if not verify_admin(username, current_password):
            return False, "Incorrect current password"

        salt = secrets.token_hex(16)
        hashed_new_password = hashlib.sha256((salt + new_password).encode()).hexdigest()
        admin_users = db["admin_users"]
        
        # Update both field types for maximum compatibility
        result = admin_users.update_one(
            {"username": username}, 
            {"$set": {
                "password": hashed_new_password, 
                "hashed_password": hashed_new_password,
                "salt": salt
            }}
        )
        
        if result.modified_count > 0:
            return True, "Password changed successfully"
        else:
            return False, "Failed to change password"
    except Exception as e:
        return False, f"Error in change_admin_password: {str(e)}"

def update_campaign_dates(voting_end_date, campaign_end_date):
    """Updates or creates the campaign end dates."""
    db = connect_to_mongodb()
    if db is None:
        return

    app_settings = db["app_settings"]
    app_settings.update_one({}, {"$set": {"voting_end_date": voting_end_date, "campaign_end_date": campaign_end_date}}, upsert=True)

def get_campaign_dates():
    """Retrieves the campaign end dates."""
    db = connect_to_mongodb()
    if db is None:
        return datetime.now() + timedelta(days=7), datetime.now() + timedelta(days=14)

    app_settings = db["app_settings"].find_one({})
    if app_settings:
        return app_settings.get("voting_end_date", datetime.now() + timedelta(days=7)), app_settings.get("campaign_end_date", datetime.now() + timedelta(days=14))
    else:
        return datetime.now() + timedelta(days=7), datetime.now() + timedelta(days=14)

def reset_campaign():
    """Resets all votes and registrations."""
    db = connect_to_mongodb()
    if db is None:
        return

    db["cities"].update_many({}, {"$set": {"votes": 0, "registrations": 0}})
    db["voter_records"].delete_many({})
    db["registrations"].delete_many({})
    update_campaign_dates(datetime.now() + timedelta(days=7), datetime.now() + timedelta(days=14))

def add_new_city(city_name):
    """Adds a new city to the database."""
    db = connect_to_mongodb()
    if db is None:
        return False, "Database connection error"

    cities = db["cities"]
    if cities.find_one({"name": city_name}):
        return False, f"City '{city_name}' already exists"

    import random
    waste_index = random.randint(30, 95)
    cities.insert_one({"name": city_name, "waste_index": waste_index, "votes": 0, "registrations": 0})
    return True, f"City '{city_name}' added successfully"

def update_city_waste_index(city_name, waste_index):
    """Updates the waste index for a city."""
    db = connect_to_mongodb()
    if db is None:
        return False, "Database connection error"

    cities = db["cities"]
    result = cities.update_one({"name": city_name}, {"$set": {"waste_index": int(waste_index)}})
    if result.modified_count > 0:
        return True, f"Waste index for '{city_name}' updated successfully"
    else:
        return False, f"City '{city_name}' not found"

def delete_city(city_name):
    """Deletes a city from the database."""
    db = connect_to_mongodb()
    if db is None:
        return False, "Database connection error"

    cities = db["cities"]
    result = cities.delete_one({"name": city_name})
    if result.deleted_count > 0:
        # Also remove any associated votes and registrations
        db["voter_records"].delete_many({"city": city_name})
        db["registrations"].delete_many({"city": city_name})
        return True, f"City '{city_name}' deleted successfully"
    else:
        return False, f"City '{city_name}' not found"

def get_registration_stats():
    """Retrieves registration statistics."""
    db = connect_to_mongodb()
    if db is None:
        return None

    registrations = db["registrations"]
    total_registrations = registrations.count_documents({})
    by_city = list(registrations.aggregate([{"$group": {"_id": "$city", "count": {"$sum": 1}}}]))
    by_time_slot = list(registrations.aggregate([{"$group": {"_id": "$time_slot", "count": {"$sum": 1}}}]))

    return {"total": total_registrations, "by_city": by_city, "by_time_slot": by_time_slot}

def delete_waste_report(report_id):
    """Deletes a waste report by its ID."""
    db = connect_to_mongodb()
    if db is None:
        return False, "Database connection error"

    waste_reports = db["waste_reports"]
    result = waste_reports.delete_one({"_id": ObjectId(report_id)})
    if result.deleted_count > 0:
        return True, "Report deleted successfully"
    else:
        return False, "Report not found"

def tag_bbmp_waste_report(report_id, tag_status):
    """Tags or untags a waste report for BBMP attention."""
    db = connect_to_mongodb()
    if db is None:
        return False, "Database connection error"

    waste_reports = db["waste_reports"]
    result = waste_reports.update_one({"_id": ObjectId(report_id)}, {"$set": {"tag_bbmp": tag_status}})
    if result.modified_count > 0:
        return True, f"Report {'tagged' if tag_status else 'untagged'} successfully"
    else:
        return False, "Report not found"

def get_waste_reports():
    """Fetches all waste reports."""
    db = connect_to_mongodb()
    if db is None:
        return []

    try:
        waste_reports_collection = db["waste_reports"]
        reports = list(waste_reports_collection.find().sort("created_at", pymongo.DESCENDING))
        return reports
    except Exception as e:
        print(f"Error retrieving waste reports: {e}")
        return []

def get_cities_data():
    """Retrieves all cities data."""
    db = connect_to_mongodb()
    if db is None:
        return []

    cities_collection = db["cities"]
    cities = list(cities_collection.find())
    return cities

def record_vote(city_name):
    """Records a vote for a city without requiring user ID."""
    db = connect_to_mongodb()
    if db is None:
        return False, "Database connection error"

    # Generate a unique session ID if needed
    user_id = "anonymous_user"
    
    voter_records = db["voter_records"]
    existing_vote = voter_records.find_one({"user_id": user_id})

    if existing_vote:
        if existing_vote["city"] != city_name:
            db["cities"].update_one({"name": existing_vote["city"]}, {"$inc": {"votes": -1}})
            voter_records.update_one({"user_id": user_id}, {"$set": {"city": city_name}})
            db["cities"].update_one({"name": city_name}, {"$inc": {"votes": 1}})
            return True, "Vote changed successfully!"
        else:
            return False, "You have already voted for this city"
    else:
        voter_records.insert_one({"user_id": user_id, "city": city_name, "timestamp": datetime.now()})
        db["cities"].update_one({"name": city_name}, {"$inc": {"votes": 1}})
        return True, "Vote recorded successfully!"

def record_registration(name, email, city="Unknown", time_slot="Any Time"):
    """Records a user's registration."""
    db = connect_to_mongodb()
    if db is None:
        return False, "Database connection error"

    # Create registration data
    registration_data = {
        "name": name,
        "email": email,
        "user_id": "anonymous_user",
        "timestamp": datetime.now(),
        "city": city,
        "time_slot": time_slot
    }

    registrations = db["registrations"]
    result = registrations.insert_one(registration_data)

    if result.inserted_id:
        # Update city registration count
        db["cities"].update_one({"name": city}, {"$inc": {"registrations": 1}})
        return True, "Registration successful!"
    else:
        return False, "Registration failed"

def record_waste_report(report_data, user_id="anonymous_user"):
    """Records a new waste report."""
    db = connect_to_mongodb()
    if db is None:
        return False

    report_data["user_id"] = user_id
    report_data["created_at"] = datetime.now()
    report_data["upvotes"] = 0
    report_data["comments"] = []

    waste_reports = db["waste_reports"]
    result = waste_reports.insert_one(report_data)

    return result.inserted_id is not None

def upvote_report(report_id, user_id="anonymous_user"):
    """Increments the upvotes for a waste report."""
    db = connect_to_mongodb()
    if db is None:
        return False, "Database connection error"

    waste_reports = db["waste_reports"]
    result = waste_reports.update_one({"_id": ObjectId(report_id)}, {"$inc": {"upvotes": 1}})

    if result.modified_count > 0:
        return True, "Upvoted successfully!"
    else:
        return False, "Failed to upvote"

def add_comment(report_id, comment_text, user_id="anonymous_user"):
    """Adds a comment to a waste report."""
    db = connect_to_mongodb()
    if db is None:
        return False, "Database connection error"

    comment = {
        "user_id": user_id,
        "text": comment_text,
        "timestamp": datetime.now()
    }

    waste_reports = db["waste_reports"]
    result = waste_reports.update_one({"_id": ObjectId(report_id)}, {"$push": {"comments": comment}})

    if result.modified_count > 0:
        return True, "Comment added successfully!"
    else:
        return False, "Failed to add comment"

def initialize_cities_data():
    """Initializes the cities data if the collection is empty."""
    db = connect_to_mongodb()
    if db is None:
        return

    cities_collection = db["cities"]

    if cities_collection.count_documents({}) == 0:
        cities_data = [
            {"name": "Bangalore", "waste_index": 85, "votes": 0, "registrations": 0},
            {"name": "Mumbai", "waste_index": 78, "votes": 0, "registrations": 0},
            {"name": "Chennai", "waste_index": 72, "votes": 0, "registrations": 0},
            {"name": "Delhi", "waste_index": 90, "votes": 0, "registrations": 0},
            {"name": "Kolkata", "waste_index": 82, "votes": 0, "registrations": 0},
            {"name": "Hyderabad", "waste_index": 75, "votes": 0, "registrations": 0},
            {"name": "Pune", "waste_index": 70, "votes": 0, "registrations": 0},
            {"name": "Ahmedabad", "waste_index": 80, "votes": 0, "registrations": 0}
        ]
        cities_collection.insert_many(cities_data)

def resolve_waste_report(report_id, resolved=True):
    """
    Mark a waste report as resolved or unresolved.
    
    Args:
        report_id (str): The ID of the waste report to update
        resolved (bool, optional): Whether to mark as resolved or unresolved. Defaults to True.
    
    Returns:
        tuple: (success, message) where success is a boolean indicating if the operation was successful,
                and message is a string with details about the operation
    """
    try:
        db = connect_to_mongodb()
        if db is None:
            return False, "Database connection error"
            
        # Check if report exists
        report = db["waste_reports"].find_one({"_id": ObjectId(report_id)})
        if not report:
            return False, "Report not found"
        
        # Update the report's resolved status
        result = db["waste_reports"].update_one(
            {"_id": ObjectId(report_id)},
            {"$set": {"resolved": resolved, "resolved_at": datetime.now()}}
        )
        
        if result.modified_count > 0:
            status = "resolved" if resolved else "unresolved"
            return True, f"Report marked as {status} successfully"
        else:
            return False, "No changes made to the report"
            
    except Exception as e:
        return False, f"Error resolving waste report: {str(e)}"
