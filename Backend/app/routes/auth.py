from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app.extensions import mongo
from app.models import User
from bson import ObjectId
import logging

bp = Blueprint('auth', __name__)
logger = logging.getLogger(__name__)

@bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        # Validate input
        if not data or not all(k in data for k in ('username', 'email', 'password')):
            return jsonify({'error': 'Missing required fields'}), 400
        
        username = data['username']
        email = data['email']
        password = data['password']
        role = data.get('role', 'Viewer')
        
        # Validate role
        if role not in ['Admin', 'Viewer']:
            return jsonify({'error': 'Invalid role'}), 400
        
        # Check if user exists
        existing_user = mongo.db.users.find_one({'email': email})
        if existing_user:
            return jsonify({'error': 'Email already exists'}), 400
        
        # Create user
        user_data = User.create(username, email, password, role)
        result = mongo.db.users.insert_one(user_data)
        
        logger.info(f"New user registered: {email}")
        
        return jsonify({
            'message': 'User registered successfully',
            'user': {
                'id': str(result.inserted_id),
                'username': username,
                'email': email,
                'role': role
            }
        }), 201
        
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        # Validate input
        if not data or not all(k in data for k in ('email', 'password')):
            return jsonify({'error': 'Missing required fields'}), 400
        
        email = data['email']
        password = data['password']
        
        # Find user
        user = mongo.db.users.find_one({'email': email})
        if not user:
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Verify password
        if not User.verify_password(user['password'], password):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Create access token
        access_token = create_access_token(
            identity=str(user['_id']),
            additional_claims={'role': user['role']}
        )
        
        logger.info(f"User logged in: {email}")
        
        return jsonify({
            'message': 'Login successful',
            'token': access_token,
            'user': {
                'id': str(user['_id']),
                'username': user['username'],
                'role': user['role']
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    try:
        user_id = get_jwt_identity()
        logger.info(f"User logged out: {user_id}")
        
        return jsonify({'message': 'Logout successful'}), 200
        
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    try:
        user_id = get_jwt_identity()
        user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'user': {
                'id': str(user['_id']),
                'username': user['username'],
                'email': user['email'],
                'role': user['role']
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get current user error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500