import random
import string

from flask import render_template_string
from flask_jwt_extended import create_access_token, create_refresh_token
from flask_mail import Message

from app import mail
from app.Repository.UserRepo import UserRepository, PasswordResetCode

from app.Utils.utils import hash_password, verify_password


class AuthController:
    @staticmethod
    def set_password(db, email, new_password):
        user = UserRepository.find_by_email(db, email)
        if not user:
            return {'error': f'Email {email} not found'}, 404

        hashed_password = hash_password(new_password)
        UserRepository.update_password(db, email, hashed_password)

        return {'message': 'Password reset successful'}, 200

    @staticmethod
    def verify_code(db, email, code):
        stored_code = PasswordResetCode.find_code(db, email, code)
        if not stored_code:
            return {'error': 'Invalid verification code'}, 400
        return {'message': 'Verification code is valid'}, 200

    def reset_password(self, email, new_password):
        user = UserRepository.find_by_email(self, email)
        if not user:
            return {'error': 'Email not found'}, 404

        hashed_password = hash_password(new_password)
        UserRepository.update_password(self, email, hashed_password)

        return {'message': 'Password reset successful'}, 200

    @staticmethod
    def forgot_password(db, email):
        user = UserRepository.find_by_email(db, email)
        if not user:
            return {'error': 'Email not found'}, 404

        new_verification_code = generate_random_code()
        PasswordResetCode.insert_code(db, email, new_verification_code)

        subject = "Password Reset Verification Code"
        send_email1(email, subject, new_verification_code)

        return {'message': 'Verification code sent to your email'}, 200

    @staticmethod
    def signup(hotel, email, name, lastname, password, role="User"):
        if not (email and name and lastname and password):
            return {'message': 'Missing information'}, 400

        existing_user = UserRepository.find_by_email(hotel, email)
        if existing_user:
            return {'message': 'Email already exists'}, 409

        user_id = UserRepository.create_user(hotel, email, password, name, lastname, role=role)
        return {'message': 'User created successfully', 'user_id': str(user_id)}, 201

    @staticmethod
    def signin(db, email, password):
        user = UserRepository.find_by_email(db, email)
        if user and verify_password(user['password'], password):
            access_token = create_access_token(identity=email)
            refresh_token = create_refresh_token(identity=email)
            user_data = {
                "password": user['password'],
                "name": user['name'],
                "email": user['email'],
                "role": user['role'],
                "_id": str(user['_id'])  # Assuming MongoDB usage
            }
            return {"token": access_token, "user": user_data, "refresh": refresh_token}, 200
        else:
            return {'error': 'Invalid credentials'}, 401


def send_email1(recipient, subject, verification_code):
    # Read the HTML template from the mail.html file
    with open('app/Utils/Mail.html', 'r') as file:
        html_content = file.read()

    # Render the HTML template with the verification code
    html_content = render_template_string(html_content, verification_code=verification_code, email=recipient)

    # Send the email
    msg = Message(subject, recipients=[recipient])
    msg.html = html_content
    mail.send(msg)

def send_refusal_email1(recipient, subject, name):
    with open(
            'app/Utils/MailRefusal.html',
            'r') as file:
        html_content = file.read()

    # Render the HTML template with the first name and last name
    html_content = render_template_string(html_content, name=name)

    # Send the email
    msg = Message(subject, recipients=[recipient])
    msg.html = html_content
    mail.send(msg)
def send_accept_email(recipient, subject, name):
    # Assuming you have a template named 'MailRefuse.html' for refusal emails
    with open('app/Utils/MailAccept.html', 'r') as file:
        html_content = file.read()

    # Render the HTML template with the first name and last name
    html_content = render_template_string(html_content, name=name)

    # Send the email
    msg = Message(subject, recipients=[recipient])
    msg.html = html_content
    mail.send(msg)


# Function to generate a random verification code
def generate_random_code(length=4):
    characters = string.digits  # Use digits only
    return ''.join(random.choice(characters) for _ in range(length))


def send_email(recipient, subject, body):
    msg = Message(subject, recipients=[recipient])
    msg.body = body
    mail.send(msg)
# Function to send an email with the verification code
