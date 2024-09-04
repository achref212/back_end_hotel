# detailController.py

from flask import request
from bson import ObjectId

from app.Models.ProfileDetail import detailModel


class detailController:
    def __init__(self, db):
        self.model = detailModel(db.db)

    def create_detail(self):
        data = request.get_json()
        detail_id = self.model.create_detail(data)
        return {'detail_id': str(detail_id)}

    def get_all_details(self):
        details = self.model.collection.find()
        serialized_details = []
        for detail in details:
            detail['_id'] = str(detail['_id'])  # Convert ObjectId to string
            serialized_details.append(detail)
        return serialized_details

    def get_detail_by_id(self, detail_id):
        detail = self.model.get_detail_by_id(ObjectId(detail_id))
        if detail:
            detail['_id'] = str(detail['_id'])  # Convert ObjectId to string
            return detail
        else:
            return {'error': 'detail not found'}

    def update_detail(self, detail_id):
        data = request.get_json()
        result = self.model.update_detail(ObjectId(detail_id), data)
        return {'modified_count': result.modified_count}

    def delete_detail(self, detail_id):
        result = self.model.delete_detail(ObjectId(detail_id))
        return {'deleted_count': result.deleted_count}
