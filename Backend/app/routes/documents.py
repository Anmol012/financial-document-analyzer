from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from werkzeug.utils import secure_filename
from app.extensions import mongo
from app.models import Document
from app.tasks.analysis_tasks import analyze_document_task
from bson import ObjectId
import os
import logging
from datetime import datetime

bp = Blueprint('documents', __name__)
logger = logging.getLogger(__name__)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}
MAX_FILE_SIZE = 104857600  # 100MB

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.route('/upload', methods=['POST'])
@jwt_required()
def upload_document():
    try:
        user_id = get_jwt_identity()
        
        # Check if file is in request
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file format. Only PDF files are allowed'}), 400
        
        # Check file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > MAX_FILE_SIZE:
            return jsonify({'error': 'File size exceeds maximum limit of 100MB'}), 400
        
        # Save file
        filename = secure_filename(file.filename)
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{timestamp}_{filename}"
        file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
        file.save(file_path)
        
        # Get document name from request or use filename
        document_name = request.form.get('name', filename)
        
        # Create document record
        document_data = Document.create(document_name, user_id, file_path, file_size)
        result = mongo.db.documents.insert_one(document_data)
        
        logger.info(f"Document uploaded: {unique_filename} by user {user_id}")
        
        return jsonify({
            'message': 'Document uploaded',
            'document': {
                'id': str(result.inserted_id),
                'name': document_name,
                'uploadDate': document_data['upload_date'].isoformat() + 'Z',
                'status': document_data['status']
            }
        }), 201
        
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@bp.route('', methods=['GET'])
@jwt_required()
def get_documents():
    try:
        user_id = get_jwt_identity()
        claims = get_jwt()
        user_role = claims.get('role', 'Viewer')
        
        # Get query parameters
        search = request.args.get('search', '')
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))
        skip = (page - 1) * limit
        
        # Build query
        query = {}
        if user_role != 'Admin':
            query['user_id'] = ObjectId(user_id)
        
        if search:
            query['name'] = {'$regex': search, '$options': 'i'}
        
        # Get documents
        documents_cursor = mongo.db.documents.find(query).sort('upload_date', -1).skip(skip).limit(limit)
        total = mongo.db.documents.count_documents(query)
        
        documents = []
        for doc in documents_cursor:
            documents.append({
                'id': str(doc['_id']),
                'name': doc['name'],
                'uploadDate': doc['upload_date'].isoformat() + 'Z',
                'status': doc['status'],
                'analysisId': str(doc['analysis_id']) if doc.get('analysis_id') else None
            })
        
        return jsonify({
            'documents': documents,
            'total': total,
            'page': page
        }), 200
        
    except Exception as e:
        logger.error(f"Get documents error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@bp.route('/<document_id>', methods=['GET'])
@jwt_required()
def get_document(document_id):
    try:
        user_id = get_jwt_identity()
        claims = get_jwt()
        user_role = claims.get('role', 'Viewer')
        
        # Find document
        document = mongo.db.documents.find_one({'_id': ObjectId(document_id)})
        
        if not document:
            return jsonify({'error': 'Document not found'}), 404
        
        # Check permissions
        if user_role != 'Admin' and str(document['user_id']) != user_id:
            return jsonify({'error': 'Forbidden'}), 403
        
        return jsonify({
            'document': {
                'id': str(document['_id']),
                'name': document['name'],
                'uploadDate': document['upload_date'].isoformat() + 'Z',
                'status': document['status'],
                'analysisId': str(document['analysis_id']) if document.get('analysis_id') else None,
                'fileSize': document['file_size']
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get document error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@bp.route('/<document_id>/analyze', methods=['POST'])
@jwt_required()
def analyze_document(document_id):
    try:
        user_id = get_jwt_identity()
        claims = get_jwt()
        user_role = claims.get('role', 'Viewer')
        
        # Find document
        document = mongo.db.documents.find_one({'_id': ObjectId(document_id)})
        
        if not document:
            return jsonify({'error': 'Document not found'}), 404
        
        # Check permissions
        if user_role != 'Admin' and str(document['user_id']) != user_id:
            return jsonify({'error': 'Forbidden'}), 403
        
        # Get options from request
        data = request.get_json() or {}
        options = data.get('options', {})
        
        # Trigger analysis task
        task = analyze_document_task.delay(document_id, user_id, options)
        
        logger.info(f"Analysis started for document {document_id}")
        
        return jsonify({
            'message': 'Analysis started',
            'analysisId': f"analysis_{document_id}"
        }), 202
        
    except Exception as e:
        logger.error(f"Analyze document error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@bp.route('/<document_id>/result', methods=['GET'])
@jwt_required()
def get_analysis_result(document_id):
    try:
        user_id = get_jwt_identity()
        claims = get_jwt()
        user_role = claims.get('role', 'Viewer')
        
        # Find document
        document = mongo.db.documents.find_one({'_id': ObjectId(document_id)})
        
        if not document:
            return jsonify({'error': 'Document not found'}), 404
        
        # Check permissions
        if user_role != 'Admin' and str(document['user_id']) != user_id:
            return jsonify({'error': 'Forbidden'}), 403
        
        # Find analysis
        if not document.get('analysis_id'):
            return jsonify({'error': 'Analysis not found or incomplete'}), 404
        
        analysis = mongo.db.analyses.find_one({'_id': document['analysis_id']})
        
        if not analysis:
            return jsonify({'error': 'Analysis not found or incomplete'}), 404
        
        return jsonify({
            'analysis': {
                'id': str(analysis['_id']),
                'documentId': str(analysis['document_id']),
                'results': analysis['results'],
                'confidence': analysis['confidence'],
                'completedAt': analysis['completed_at'].isoformat() + 'Z' if analysis.get('completed_at') else None,
                'status': analysis['status']
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get analysis result error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@bp.route('/<document_id>', methods=['DELETE'])
@jwt_required()
def delete_document(document_id):
    try:
        user_id = get_jwt_identity()
        claims = get_jwt()
        user_role = claims.get('role', 'Viewer')
        
        # Find document
        document = mongo.db.documents.find_one({'_id': ObjectId(document_id)})
        
        if not document:
            return jsonify({'error': 'Document not found'}), 404
        
        # Check permissions
        if user_role != 'Admin' and str(document['user_id']) != user_id:
            return jsonify({'error': 'Forbidden'}), 403
        
        # Delete file
        if os.path.exists(document['file_path']):
            os.remove(document['file_path'])
        
        # Delete analysis if exists
        if document.get('analysis_id'):
            mongo.db.analyses.delete_one({'_id': document['analysis_id']})
        
        # Delete document
        mongo.db.documents.delete_one({'_id': ObjectId(document_id)})
        
        logger.info(f"Document deleted: {document_id}")
        
        return jsonify({'message': 'Document deleted'}), 200
        
    except Exception as e:
        logger.error(f"Delete document error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@bp.route('/<document_id>/download', methods=['GET'])
@jwt_required()
def download_document(document_id):
    try:
        user_id = get_jwt_identity()
        claims = get_jwt()
        user_role = claims.get('role', 'Viewer')
        
        # Find document
        document = mongo.db.documents.find_one({'_id': ObjectId(document_id)})
        
        if not document:
            return jsonify({'error': 'Document not found'}), 404
        
        # Check permissions
        if user_role != 'Admin' and str(document['user_id']) != user_id:
            return jsonify({'error': 'Forbidden'}), 403
        
        # Check if file exists
        if not os.path.exists(document['file_path']):
            return jsonify({'error': 'File not found'}), 404
        
        return send_file(
            document['file_path'],
            as_attachment=True,
            download_name=document['name']
        )
        
    except Exception as e:
        logger.error(f"Download document error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500