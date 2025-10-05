from datetime import datetime
from bson import ObjectId
import bcrypt

class User:
    @staticmethod
    def create(username, email, password, role='Viewer'):
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        return {
            'username': username,
            'email': email,
            'password': hashed_password,
            'role': role,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
    
    @staticmethod
    def verify_password(stored_password, provided_password):
        return bcrypt.checkpw(provided_password.encode('utf-8'), stored_password)

class Document:
    @staticmethod
    def create(name, user_id, file_path, file_size):
        return {
            'name': name,
            'user_id': ObjectId(user_id),
            'file_path': file_path,
            'file_size': file_size,
            'status': 'pending',
            'upload_date': datetime.utcnow(),
            'analysis_id': None,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
    
    @staticmethod
    def update_status(status, analysis_id=None):
        update_data = {
            'status': status,
            'updated_at': datetime.utcnow()
        }
        if analysis_id:
            update_data['analysis_id'] = ObjectId(analysis_id)
        return update_data

class Analysis:
    @staticmethod
    def create(document_id, user_id):
        return {
            'document_id': ObjectId(document_id),
            'user_id': ObjectId(user_id),
            'status': 'analyzing',
            'results': {},
            'confidence': 0.0,
            'started_at': datetime.utcnow(),
            'completed_at': None,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
    
    @staticmethod
    def update_results(results, confidence, status='complete'):
        return {
            'results': results,
            'confidence': confidence,
            'status': status,
            'completed_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }