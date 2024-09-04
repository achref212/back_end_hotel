from app.Models.userModel import User
from app.Repository import UserRepo
from app.Repository.UserRepo import UserRepository


class UserController:
    @staticmethod
    def edit_user(db, user_id, **kwargs):
        # Find the user by ID
        user = UserRepo.UserRepository.get_by_id(db, user_id)
        if not user:
            return "User not found", 404

        # Update fields if they are provided in kwargs
        if 'email' in kwargs:
            user.email = kwargs['email']
        if 'birthdate' in kwargs:
            user.birthdate = kwargs['birthdate']
        if 'password' in kwargs:
            user.password = kwargs['password']  # Consider hashing the password before saving
        if 'lastname' in kwargs:
            user.lastname = kwargs['lastname']
        if 'name' in kwargs:
            user.name = kwargs['name']
        if 'profile_picture' in kwargs:
            user.profile_picture = kwargs['profile_picture']
        if 'role' in kwargs:
            user.role = kwargs['role']

        update_result = db.db.users.update_one({"_id": user_id}, {"$set": user})
        if update_result.modified_count > 0:
            return "User updated successfully", 200
        else:
            return "User update failed", 500

    @staticmethod
    def get_all_users(db):
        users = UserRepo.UserRepository.find_all(db)
        serialized_users = []
        for user in users:
            user['_id'] = str(user['_id'])  # Convert ObjectId to string
            serialized_users.append(user)
        return serialized_users
