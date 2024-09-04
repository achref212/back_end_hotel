from datetime import datetime
from flask import request, jsonify
from bson import ObjectId
from app.Controllers.ReviewController import ReviewController
from app import api, mongo, app
from flask_restx import Resource, fields
from app.Repository import UserRepo

review_controller = ReviewController(mongo)
db = mongo.db

# Define the review model without roomId and activityId
review_model = api.model('Review', {
    'userId': fields.String(required=True, description='User ID'),
    'rating': fields.Integer(required=True, description='Rating (1-5)'),
    'comment': fields.String(required=True, description='Comment'),
    'createdAt': fields.DateTime(description='Review Date', readonly=True)
})

@app.route('/reviews/', methods=['POST'])
def create_review():
    try:
        data = request.get_json()

        # Verify that userId is provided
        if 'userId' not in data:
            return jsonify({'error': 'Missing userId'}), 400

        # Verify user existence
        user_id = ObjectId(data['userId'])
        user = UserRepo.UserRepository.get_by_id(mongo, user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        # Add the createdAt field
        data['createdAt'] = datetime.utcnow()

        # Insert the review into the database
        review_id = db.Reviews.insert_one(data).inserted_id
        return jsonify({'message': 'Review created successfully', 'review_id': str(review_id)}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/reviews/', methods=['GET'])
def get_all_reviews():
    try:
        reviews = db.Reviews.find()
        results = []
        for review in reviews:
            review['_id'] = str(review['_id'])  # Convert ObjectId to string for JSON serialization
            results.append(review)
        return jsonify(results), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/reviews/<string:review_id>', methods=['GET'])
def get_review_by_id(review_id):
    try:
        review = db.Reviews.find_one({'_id': ObjectId(review_id)})
        if review:
            review['_id'] = str(review['_id'])  # Convert ObjectId to string for JSON serialization
            return jsonify(review), 200
        else:
            return jsonify({'message': 'Review not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/reviews/<string:review_id>', methods=['DELETE'])
def delete_review(review_id):
    try:
        result = db.Reviews.delete_one({'_id': ObjectId(review_id)})
        if result.deleted_count > 0:
            return jsonify({'message': 'Review deleted successfully'}), 200
        else:
            return jsonify({'message': 'Review not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/reviews/<string:review_id>', methods=['PUT'])
def update_review(review_id):
    try:
        data = request.get_json()
        if not data:
            return jsonify({'message': 'No update data provided'}), 400

        result = db.Reviews.update_one({'_id': ObjectId(review_id)}, {'$set': data})
        if result.modified_count > 0:
            return jsonify({'message': 'Review updated successfully'}), 200
        else:
            return jsonify({'message': 'No changes made or review not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/reviews/user/<string:user_id>', methods=['GET'])
def get_reviews_by_user(user_id):
    try:
        reviews = db.Reviews.find({'userId': user_id})
        results = []
        for review in reviews:
            review['_id'] = str(review['_id'])  # Convert ObjectId to string for JSON serialization
            results.append(review)
        if results:
            return jsonify(results), 200
        else:
            return jsonify({'message': 'No reviews found for this user'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500
