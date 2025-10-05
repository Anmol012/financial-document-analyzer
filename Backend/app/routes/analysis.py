from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.extensions import mongo
from app.utils.export_utils import generate_pdf_report, generate_csv_report
from bson import ObjectId
import logging
import os
import tempfile

bp = Blueprint('analysis', __name__)
logger = logging.getLogger(__name__)

@bp.route('/history', methods=['GET'])
@jwt_required()
def get_analysis_history():
    try:
        user_id = get_jwt_identity()
        claims = get_jwt()
        user_role = claims.get('role', 'Viewer')
        
        # Get query parameters
        document_id = request.args.get('documentId')
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))
        skip = (page - 1) * limit
        
        # Build query
        query = {}
        if user_role != 'Admin':
            query['user_id'] = ObjectId(user_id)
        
        if document_id:
            query['document_id'] = ObjectId(document_id)
        
        # Get analyses
        analyses_cursor = mongo.db.analyses.find(query).sort('completed_at', -1).skip(skip).limit(limit)
        total = mongo.db.analyses.count_documents(query)
        
        history = []
        for analysis in analyses_cursor:
            # Get document name
            document = mongo.db.documents.find_one({'_id': analysis['document_id']})
            document_name = document['name'] if document else 'Unknown'
            
            history.append({
                'id': str(analysis['_id']),
                'documentName': document_name,
                'completedAt': analysis['completed_at'].isoformat() + 'Z' if analysis.get('completed_at') else None,
                'status': analysis['status']
            })
        
        return jsonify({
            'history': history,
            'total': total
        }), 200
        
    except Exception as e:
        logger.error(f"Get analysis history error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@bp.route('/<analysis_id>', methods=['GET'])
@jwt_required()
def get_analysis(analysis_id):
    try:
        user_id = get_jwt_identity()
        claims = get_jwt()
        user_role = claims.get('role', 'Viewer')
        
        # Find analysis
        analysis = mongo.db.analyses.find_one({'_id': ObjectId(analysis_id)})
        
        if not analysis:
            return jsonify({'error': 'Analysis not found'}), 404
        
        # Check permissions
        if user_role != 'Admin' and str(analysis['user_id']) != user_id:
            return jsonify({'error': 'Forbidden'}), 403
        
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
        logger.error(f"Get analysis error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@bp.route('/<analysis_id>/export', methods=['GET'])
@jwt_required()
def export_analysis(analysis_id):
    try:
        user_id = get_jwt_identity()
        claims = get_jwt()
        user_role = claims.get('role', 'Viewer')
        
        # Get format parameter
        export_format = request.args.get('format', 'pdf').lower()
        
        if export_format not in ['pdf', 'csv']:
            return jsonify({'error': 'Invalid format. Use pdf or csv'}), 400
        
        # Find analysis
        analysis = mongo.db.analyses.find_one({'_id': ObjectId(analysis_id)})
        
        if not analysis:
            return jsonify({'error': 'Analysis not found'}), 404
        
        # Check permissions
        if user_role != 'Admin' and str(analysis['user_id']) != user_id:
            return jsonify({'error': 'Forbidden'}), 403
        
        # Get document info
        document = mongo.db.documents.find_one({'_id': analysis['document_id']})
        document_name = document['name'] if document else 'Unknown'
        
        # Generate export file
        temp_dir = tempfile.gettempdir()
        
        if export_format == 'pdf':
            filename = f"analysis_{analysis_id}.pdf"
            filepath = os.path.join(temp_dir, filename)
            generate_pdf_report(analysis, document_name, filepath)
            mimetype = 'application/pdf'
        else:  # csv
            filename = f"analysis_{analysis_id}.csv"
            filepath = os.path.join(temp_dir, filename)
            generate_csv_report(analysis, document_name, filepath)
            mimetype = 'text/csv'
        
        logger.info(f"Analysis exported: {analysis_id} as {export_format}")
        
        return send_file(
            filepath,
            mimetype=mimetype,
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        logger.error(f"Export analysis error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@bp.route('/<analysis_id>', methods=['DELETE'])
@jwt_required()
def delete_analysis(analysis_id):
    try:
        user_id = get_jwt_identity()
        claims = get_jwt()
        user_role = claims.get('role', 'Viewer')
        
        # Find analysis
        analysis = mongo.db.analyses.find_one({'_id': ObjectId(analysis_id)})
        
        if not analysis:
            return jsonify({'error': 'Analysis not found'}), 404
        
        # Check permissions
        if user_role != 'Admin' and str(analysis['user_id']) != user_id:
            return jsonify({'error': 'Forbidden'}), 403
        
        # Update document to remove analysis reference
        mongo.db.documents.update_one(
            {'analysis_id': ObjectId(analysis_id)},
            {'$set': {'analysis_id': None, 'status': 'pending'}}
        )
        
        # Delete analysis
        mongo.db.analyses.delete_one({'_id': ObjectId(analysis_id)})
        
        logger.info(f"Analysis deleted: {analysis_id}")
        
        return jsonify({'message': 'Analysis deleted'}), 200
        
    except Exception as e:
        logger.error(f"Delete analysis error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500