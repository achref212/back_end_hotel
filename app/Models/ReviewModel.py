from bson import ObjectId
from datetime import datetime

class ReviewModel:
    def __init__(self, db):
        self.collection = db['Reviews']

    def create_review(self, data):
        data['created_at'] = datetime.utcnow()
        return self.collection.insert_one(data).inserted_id

    def get_all_reviews(self):
        return list(self.collection.find())

    def get_review_by_id(self, review_id):
        review = self.collection.find_one({'_id': ObjectId(review_id)})
        if review:
            review['_id'] = str(review['_id'])
        return review

    def update_review(self, review_id, data):
        return self.collection.update_one({'_id': ObjectId(review_id)}, {'$set': data})

    def delete_review(self, review_id):
        return self.collection.delete_one({'_id': ObjectId(review_id)})

    def get_reviews_by_user(self, user_id):
        return list(self.collection.find({'userId': user_id}))
