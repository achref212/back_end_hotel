from bson import ObjectId

from app.Models.userModel import User
from app.Utils.utils import hash_password


class UserRepository:
    @staticmethod
    def create_user(db, email, password, name, lastname, birthdate="None", profile_picture="None",
                    role="user", google_id="None"):
        """
        Creates a new user document in the MongoDB database.
        """
        hashed_password = hash_password(password)  # Ensure this securely hashes the password
        user_data = {
            "email": email,
            "password": hashed_password,
            "name": name,
            "lastname": lastname,
            "birthdate": birthdate,
            "role": role,
            "profile_picture": profile_picture,
            "google_id": google_id
        }
        result = db.db.users.insert_one(user_data)
        user_data['_id'] = str(result.inserted_id)  # Convert ObjectId to string
        return user_data

    @staticmethod
    def update_password(db, email, hashed_password):
        db.db.users.update_one({'email': email}, {'$set': {'password': hashed_password}})

    @staticmethod
    def update_user_password(db, user_id, hashed_password):
        """
        Updates the user's password in the database.

        :param user_id: The unique identifier of the user.
        :param hashed_password: The new hashed password.
        """
        try:
            # Update the user document with the new password
            result = db.db.users.update_one({'_id': user_id}, {'$set': {'password': hashed_password}})
            return result.modified_count > 0  # Returns True if the update was successful
        except Exception as e:
            print(f"Error updating password: {e}")
            return False

    @staticmethod
    def find_all(db):
        """
        Retrieves all user documents from the MongoDB database.
        """
        users = db.users.find()
        return list(users)

    @staticmethod
    def find_by_username(db, username):
        """
        Retrieves a user document from the MongoDB database by username.
        """
        user = db.db.users.find_one({'username': username})
        return user

    @staticmethod
    def find_by_id(db, username):
        """
        Retrieves a user document from the MongoDB database by username.
        """
        user = db.db.users.find_one({'_id': username})
        return user

    @staticmethod
    def find_by_email(mongo, email):
        """
        Retrieves a user document from the MongoDB database by email.
        """
        user = mongo.db.users.find_one({'email': email})
        return user

    @staticmethod
    def get_by_id(mongo, user_id):
        user = mongo.db.users.find_one({'_id': user_id})
        return user

    @staticmethod
    def find_by_idd(mongo, user_id):
        """
        Retrieves a user document from the MongoDB database by user_id.
        """
        if user_id:
            if isinstance(user_id, str):
                user_id = ObjectId(user_id)
            user = mongo.db.users.find_one({'_id': user_id})
            if user:
                user['_id'] = str(user['_id'])  # Convert ObjectId to string for JSON serialization
            return user
        return None
class PasswordResetCode:
    @staticmethod
    def insert_code(db, email, code):
        db.db.password_reset_codes.insert_one({'email': email, 'code': code})

    @staticmethod
    def find_code(db, email, code):
        return db.db.password_reset_codes.find_one({'email': email, 'code': code})
