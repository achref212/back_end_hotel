from flask import Flask, jsonify
from flask_jwt_extended import JWTManager
from flask_mail import Mail
from flask_pymongo import PyMongo, MongoClient
from flask_restx import Api
from oauthlib import oauth2
from werkzeug.security import generate_password_hash, check_password_hash

from app.Repository.UserRepo import UserRepository
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

mongo = MongoClient(app.config['MONGO_URI'], tlsAllowInvalidCertificates=True)
api = Api(app)
mail = Mail(app)
# Initialize the JWTManager with your Flask user
jwt = JWTManager(app)


@jwt.additional_claims_loader
def add_claims_to_access_token(identity):
    # Assuming identity is the email of the user
    u = UserRepository.find_by_email(mongo, identity)
    if userRoute:
        # Ensure you handle the case where user might be None
        return {"role": u.get("role")}
    return {}


@jwt.unauthorized_loader
def missing_token_callback():
    return jsonify({
        'error': 'authorization_required',
        'message': 'Authorization token is missing'
    }), 401


# Callback function to handle expired tokens
@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({
        'error': jwt_header,
        'message': jwt_payload
    }), 401


# Callback function to handle invalid tokens
@jwt.invalid_token_loader
def invalid_token_callback(error):
    return jsonify({
        'error': 'invalid_token',
        'message': 'Signature verification failed.'
    }), 422  # 422 Unprocessable Entity for semantic correctness


# Callback function for tokens that are not fresh if you are using fresh tokens
@jwt.needs_fresh_token_loader
def token_not_fresh_callback(jwt_header, jwt_payload):
    return jsonify({
        'error': 'fresh_token_required',
        'message': 'Fresh token is required.'
    }), 401


# Callback function to handle revoked tokens
@jwt.revoked_token_loader
def revoked_token_callback(jwt_header, jwt_payload):
    return jsonify({
        'error': 'token_revoked',
        'message': 'The token has been revoked.'
    }), 401


@jwt.unauthorized_loader
def revoked_token_callback(jwt_header, jwt_payload):
    return jsonify({
        "error": "authorization_required",
        "message": "Missing Authorization Header"
    }), 401


CLIENT_ID = app.config['CLIENT_ID']
CLIENT_SECRET = app.config['CLIENT_SECRET']

DATA = {
    'response_type': "code",
    'redirect_uri': "https://localhost:5000/home",
    'scope': 'https://www.googleapis.com/auth/userinfo.email',
    'client_id': CLIENT_ID,
    'prompt': 'consent'
}

URL_DICT = {
    'google_oauth': 'https://accounts.google.com/o/oauth2/v2/auth',
    'token_gen': 'https://oauth2.googleapis.com/token',
    'get_user_info': 'https://www.googleapis.com/oauth2/v3/userinfo'
}

CLIENT = oauth2.WebApplicationClient(CLIENT_ID)

from app.Routes import userRoute, ProfileDetailRoute, RoomRoute, ReviewRoute, BookingRoute, ReservationRoute, ActivityRoute

