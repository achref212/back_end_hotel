from flask import Flask
from flask_restx import Api, Resource, fields
from pymongo import MongoClient

from app import api, mongo
from app.Controllers.profile_detail_controller import detailController

# Instantiate the controller
detail_controller = detailController(mongo)

# Define the Swagger model for a detail
detail_model = api.model('Detail', {
    'user_id': fields.String(required=True, description='User ID'),
    'social_links': fields.List(fields.Nested(api.model('SocialLink', {
        'name': fields.String(required=True, description='Social Media Name'),
        'icon': fields.String(description='Icon Representation'),  # Icons cannot be directly represented in a Flask API, so this would be a string describing the icon
        'url': fields.String(required=True, description='Social Media URL')
    })), required=True, description='List of Social Media Links'),
})

# Define the routes
@api.route('/details')
class DetailsResource(Resource):
    def get(self):
        return detail_controller.get_all_details()

    @api.expect(detail_model)
    def post(self):
        return detail_controller.create_detail()


@api.route('/details/<string:detail_id>')  # Use string:detail_id to specify that detail_id is a string
class DetailResource(Resource):
    def get(self, detail_id):
        return detail_controller.get_detail_by_id(detail_id)

    @api.expect(detail_model)
    def put(self, detail_id):
        return detail_controller.update_detail(detail_id)

    def delete(self, detail_id):
        return detail_controller.delete_detail(detail_id)
