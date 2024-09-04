from flask import request
from bson import ObjectId
from app.Models.ReviewModel import ReviewModel

class ReviewController:
    def __init__(self, db):
        self.model = ReviewModel(db)

    def create_review(self):
        data = request.get_json()
        review_id = self.model.create_review(data)
        return {'review_id': str(review_id)}

    def get_all_reviews(self):
        reviews = self.model.get_all_reviews()
        return [{'_id': str(review['_id']), **review} for review in reviews]

    def get_review_by_id(self, review_id):
        review = self.model.get_review_by_id(ObjectId(review_id))
        if review:
            review['_id'] = str(review['_id'])
            return review
        return {'error': 'Review not found'}

    def update_review(self, review_id):
        data = request.get_json()
        result = self.model.update_review(ObjectId(review_id), data)
        if result.modified_count:
            return {'message': 'Review updated successfully'}
        return {'message': 'No review was updated'}

    def delete_review(self, review_id):
        result = self.model.delete_review(ObjectId(review_id))
        if result.deleted_count:
            return {'message': 'Review deleted successfully'}
        return {'message': 'No review was deleted'}

    def get_reviews_by_user(self, user_id):
        reviews = self.model.get_reviews_by_user(user_id)
        return [{'_id': str(review['_id']), **review} for review in reviews]