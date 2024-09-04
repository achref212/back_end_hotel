import base64
import uuid
from io import BytesIO

import qrcode
from bson import ObjectId
from flask import redirect, jsonify
from flask import request
from flask_cors import CORS
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt, create_access_token, verify_jwt_in_request, \
    create_refresh_token
from flask_restx import Resource
from flask_socketio import SocketIO
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

from app import app, api, mongo, CLIENT_ID, URL_DICT, CLIENT, DATA
from app.Controllers.auth import AuthController
from app.Controllers.user_controller import UserController
from app.Models.Payloads import signin_model, signup_response_model, forgot_password_model, verify_code_model, set_password_model, \
    reset_password_model, edit_user_model
from app.Repository.UserRepo import UserRepository

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}


def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


socketio = SocketIO(api.app, cors_allowed_origins="*")

sessions = {}
CORS(api.app)


@api.route('/generate_qr')
class generate_qr(Resource):
    def get(self):
        session_id = str(uuid.uuid4())
        sessions[session_id] = {'authenticated': False}

        # Generate QR code with session ID
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(session_id)
        qr.make(fit=True)
        img = qr.make_image(fill='black', back_color='white')
        bi = BytesIO()
        img.save(bi, format="PNG")
        qr_code = base64.b64encode(bi.getvalue()).decode('utf-8')

        return jsonify({'qr_code': qr_code, 'session_id': session_id})


@socketio.on('validate_qr')
def handle_validate_qr(json):
    session_id = json['session_id']
    user_id = json['user_id']
    refresh_token = json['refresh_token']
    print(user_id)
    print(session_id)
    print(refresh_token)
    if session_id in sessions:
        print("authenticated")
        sessions[session_id]['authenticated'] = True
        socketio.emit('authenticated', {'session_id': session_id,'user_id': user_id , 'refresh_token':refresh_token})
    else:
        print(f"Session ID {session_id} not found")


@api.route('/signup')
class Signup(Resource):
    @api.expect(signup_response_model, validate=True)
    def post(self):
        """Sign in user"""
        json_data = request.json
        email = json_data.get('email')
        password = json_data.get('password')
        name = json_data.get('name')
        lastname = json_data.get('lastname')
        # Delegate to AuthController
        return AuthController.signup(mongo, email, name, lastname, password)


@api.route('/signin')
class Signin(Resource):
    @api.expect(signin_model, validate=True)
    def post(self):
        json_data = request.json
        email = json_data.get('email')
        password = json_data.get('password')

        # Delegate to AuthController
        return AuthController.signin(mongo, email, password)


# Assuming you have the necessary imports and api setup
@api.route('/tokenIsValid')
class token_is_valid(Resource):
    @jwt_required()
    def get(self):
        try:
            verify_jwt_in_request()
            user_id = get_jwt_identity()
            u = UserRepository.find_by_email(mongo, user_id)
            u['_id'] = str(u['_id'])
            access_token = create_access_token(identity=user_id)

            return {"valid": True, "user": u, "token": access_token}, 200
        except Exception as e:
            return {"valid": False, "message": str(e)}, 401


@api.route('/refreshToken')
class RefreshToken(Resource):
    @jwt_required(refresh=True)
    def post(self):
        current_user = get_jwt_identity()
        new_token = create_access_token(identity=current_user)
        return {'access_token': new_token}, 200



# Assuming necessary imports are already done

@api.route('/users')
class UserList(Resource):
    # @jwt_required()
    def get(self):
        # Directly using mongo.db might require you to import or access the database instance appropriately
        serialized_users = UserController.get_all_users(mongo.db)
        return serialized_users, 200


@api.route('/forgot_password')
class ForgotPassword(Resource):
    @api.expect(forgot_password_model, validate=True)
    def post(self):
        """Forgot password"""
        email = request.json.get('email')
        return AuthController.forgot_password(mongo, email)


@api.route('/otp-verif')
class ForgotPassword(Resource):
    @api.expect(forgot_password_model, validate=True)
    def post(self):
        """Forgot password"""
        email = request.json.get('email')
        return AuthController.otp_verif(mongo, email)


@api.route('/reset_password')
class ResetPassword(Resource):
    @api.expect(reset_password_model, validate=True)
    def post(self):
        """Reset password"""
        json_data = request.json
        email = json_data['email']
        new_password = json_data['new_password']

        # Delegate to AuthController
        return AuthController.reset_password(mongo, email, new_password)

    @api.route('/ping')
    class ping(Resource):
        def post(self):
            """Reset password"""

            # Send a ping to confirm a successful connection
            try:
                res = mongo.admin.command('ping')
                print("Pinged your deployment. You successfully connected to MongoDB!")
            except Exception as e:
                print(e)
                return 401

            # Delegate to AuthController
            return 200

    @api.route('/set-password')
    class SetPassword(Resource):

        @api.expect(set_password_model, validate=True)
        def post(self):
            """Reset password"""
            json_data = request.json
            email = json_data['email']
            new_password = json_data['password']

            # Delegate the business logic to the AuthController
            return AuthController.set_password(mongo, email, new_password)

    @api.route('/verify_code')
    class VerifyCode(Resource):
        @api.expect(verify_code_model, validate=True)
        def post(self):
            """Verify verification code"""
            json_data = request.json
            email = json_data['email']
            code = json_data['code']

            # Delegate business logic to the AuthController
            return AuthController.verify_code(mongo, email, code)


def exchange_token(code):
    try:
        # Exchange the authorization code for an ID token
        id_token_info = id_token.verify_oauth2_token(
            code,
            google_requests.Request(),
            CLIENT_ID
        )

        # Verify the issuer
        if id_token_info['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            raise ValueError('Wrong issuer.')

        # Return the ID token info
        return id_token_info

    except ValueError as e:
        print("Error verifying ID token:", str(e))
        return None


@api.route('/google-sign-in', methods=['GET', 'POST'])
class GoogleSignIn(Resource):
    def post(self):
        # Check if the request is JSON or form-encoded

        if request.is_json:
            code = request.get_json().get('code')
        else:
            code = request.form.get('code')

        print(code)

        # Redirect to Google Sign-In if 'code' parameter is missing
        if not code:
            google_signin_url = CLIENT.prepare_request_uri(
                URL_DICT['google_oauth'],
                redirect_uri=DATA['redirect_uri'],
                scope=DATA['scope'],
                prompt=DATA['prompt']
            )
            return redirect(google_signin_url)

        # Exchange authorization code for ID token
        id_token_info = exchange_token(code)

        if id_token_info is None:
            return "Error during token exchange", 400

        # Extract necessary information from the ID token info
        email = id_token_info.get('email')
        sub = id_token_info.get('sub')  # Google user ID
        name = id_token_info.get('name')
        picture = id_token_info.get('picture')

        # Placeholder or user-provided values for missing fields from Google
        birthdate = "Not provided"  # Placeholder, consider updating your model or UX to collect this
        title = "Not provided"  # Placeholder, consider updating your model or UX to collect this
        lastname = "Not provided"  # Placeholder, consider asking the user or parsing the 'name' if possible

        # Check if user exists to prevent duplicate entries
        user = UserRepository.find_by_email(mongo, email)
        if user is None:
            # Create new user if does not exist
            user_id = UserRepository.create_user(mongo, email, "", name, lastname, title, birthdate, picture, "user",
                                                 sub)
            user_data = {
                "_id": user_id.get('_id'),
                "email": email,
                "password": "",
                "name": name,
                "lastname": lastname,
                "title": title,
                "birthdate": birthdate,
                "role": user_id.get('role'),
                "profile_picture": picture,
                "google_id": sub
            }
        else:
            # Handle existing user scenario, maybe update existing records or just fetch user details

            user_data = {
                "_id": str(user['_id']),
                "lastname": lastname,
                "title": title,
                "birthdate": birthdate,
                "role": user['role'],
                "password": user['password'],
                "name": user['name'],
                "email": user['email'],
                "profile_picture": picture,
                "google_id": sub
            }

        access_token = create_access_token(identity=email)
        refresh_token = create_refresh_token(identity=email)
        return {"token": access_token, "user": user_data, "refresh": refresh_token}, 200


@api.route('/whoami', methods=['GET'])
class WhoAmI(Resource):
    @jwt_required()
    def get(self):
        claims = get_jwt()
        # Assuming you have an 'identity' claim containing the user's email or username
        identity = get_jwt_identity()
        if identity:
            user = UserRepository.find_by_email(mongo, identity)
            if user:
                # Customize this response based on what user information you want to return
                user_info = {
                    "email": user.get("email"),
                    "name": user.get("name"),
                    "role": user.get("role")
                }
                return {"user": user_info, "claims": claims}, 200
            else:
                return {"msg": "User not found"}, 404
        else:
            return {"msg": "Invalid JWT claims"}, 400


@api.route('/edit-user/<user_id>')
class EditUser(Resource):
    @api.expect(edit_user_model, validate=True)
    def put(self, user_id):
        """
        Update user details.
        """
        try:
            # Convert user_id from string to ObjectId
            oid = ObjectId(user_id)
        except:
            return {'message': 'Invalid user ID format'}, 400

        # Proceed with the update using the oid
        result = UserController.edit_user(db=mongo, user_id=oid, **api.payload)
        if result:
            return {'message': result}, 200
        else:
            return {'message': 'User not found or update failed'}, 404
