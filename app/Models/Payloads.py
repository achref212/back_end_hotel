# Define models for request and response payloads
from flask_restx import fields

from app import api

user_model = api.model('User', {
    'email': fields.String(required=False, description='User email'),
    # 'username': fields.String(required=True, description='Username'),
    'password': fields.String(required=True, description='Password'),
    'name': fields.String(required=False, description='First name'),
    # 'last_name': fields.String(required=False, description='Last name')
})
verify_code_model = api.model('VerifyCode', {
    'email': fields.String(required=True, description='User email'),
    'code': fields.String(required=True, description='Verification code')
})

signup_response_model = api.model('SignupResponse', {
    'name': fields.String(required=True, description='name'),
    'lastname': fields.String(required=True, description='lastname'),
    'email': fields.String(required=True, description='email'),
    'password': fields.String(required=True, description='Password')
})
# Model specifically for the signin endpoint
signin_model = api.model('Signin', {
    'email': fields.String(required=True, description='email'),
    'password': fields.String(required=True, description='Password')
})
forgot_password_model = api.model('ForgotPassword', {
    'email': fields.String(required=True, description='User email')
})
reset_password_model = api.model('ResetPassword', {
    'email': fields.String(required=True, description='User email'),
    'new_password': fields.String(required=True, description='New password')
})
set_password_model = api.model('ResetPassword', {
    'email': fields.String(required=True, description='User email'),
    'password': fields.String(required=True, description='New password')
})
file_model = api.model('File', {
    'filename': fields.String(required=True, description='Filename'),

})
edit_user_model = api.model('EditUser', {
    'email': fields.String(required=False, description='The user\'s email address'),
    'birthdate': fields.String(required=False, description='The user\'s date of birth'),
    'password': fields.String(required=False, description='The user\'s new or updated password'),
    'lastname': fields.String(required=False, description='The user\'s last name'),
    'name': fields.String(required=False, description='The user\'s name'),
    'profile_picture': fields.String(required=False, description='URL to the user\'s profile picture'),
    'role': fields.String(required=False, description='The role of the user in the system'),
})
