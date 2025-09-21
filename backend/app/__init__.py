import os
import logging
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_migrate import Migrate

# Configure logging to show INFO level messages
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

db = SQLAlchemy()
jwt = JWTManager()
migrate = Migrate()

def create_app(config_name=None):
    app = Flask(__name__)
    
    # Load configuration
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')
    
    from config import config
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    
    # Initialize WebSocket
    from app.websocket import socketio
    socketio.init_app(app)
    
    # EMERGENCY FIX COMPLETE: Re-enable CORS with proper configuration
    print(f"[CORS] Re-enabling CORS after 405 fix")
    CORS(app, 
         origins="*", 
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
         allow_headers=["Content-Type", "Authorization", "X-Requested-With", "Idempotency-Key"],
         supports_credentials=False)
    print(f"[CORS] CORS re-enabled successfully")

    # Handle OPTIONS requests before authentication
    @app.before_request
    def handle_options():
        if request.method == 'OPTIONS':
            # Let Flask-CORS handle OPTIONS
            return '', 200

    # Enhanced JWT error handlers with better debugging
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        print(f"[AUTH] Token expired for user: {jwt_payload.get('sub', 'unknown')}")
        return jsonify({
            'error': {
                'code': 'TOKEN_EXPIRED',
                'message': 'Token has expired',
                'details': {
                    'expired_at': jwt_payload.get('exp'),
                    'user_id': jwt_payload.get('sub')
                }
            }
        }), 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        print(f"[AUTH] Invalid token error: {error}")
        return jsonify({
            'error': {
                'code': 'INVALID_TOKEN',
                'message': 'Invalid token',
                'details': {
                    'error': str(error)
                }
            }
        }), 401
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        print(f"[AUTH] Missing token for endpoint: {request.endpoint}")
        return jsonify({
            'error': {
                'code': 'MISSING_TOKEN',
                'message': 'Token is required',
                'details': {
                    'endpoint': request.endpoint,
                    'method': request.method
                }
            }
        }), 401
    
    # Global error handlers
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'error': {
                'code': 'BAD_REQUEST',
                'message': 'Bad request',
                'details': {}
            }
        }), 400
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'error': {
                'code': 'NOT_FOUND',
                'message': 'Resource not found',
                'details': {}
            }
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Internal server error',
                'details': {}
            }
        }), 500
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        return jsonify({'status': 'healthy', 'message': 'ERP System API is running'}), 200
    
    # REMOVED CONFLICTING GLOBAL OPTIONS HANDLER
    # The specific blueprint routes already handle OPTIONS properly via CORS
    # This global handler was causing 405 errors by overriding route methods
    
    # Simple CORS test endpoint
    @app.route('/cors-test', methods=['GET', 'OPTIONS'])
    def cors_test():
        print("[CORS TEST] Route called")
        origin = request.headers.get('Origin')
        print(f"[CORS TEST] Origin: {origin}")
        
        if request.method == 'OPTIONS':
            print("[CORS TEST] Handling OPTIONS")
            response = jsonify({})
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
            print(f"[CORS TEST] Added CORS headers")
            return response
        
        # Regular GET request
        response = jsonify({'message': 'CORS test endpoint', 'origin': origin})
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        print(f"[CORS TEST] Added CORS headers to GET response")
        return response
    
    
    # Register blueprints
    from app.routes import auth, users, suppliers, requisitions, purchase_orders, inventory, accounting, projects, storage, logistics, acceptance, delivery_management, profile, receiving, putaway

    app.register_blueprint(auth.bp)
    app.register_blueprint(users.bp)
    app.register_blueprint(profile.bp)
    app.register_blueprint(suppliers.bp)
    app.register_blueprint(requisitions.bp)
    app.register_blueprint(purchase_orders.bp)
    app.register_blueprint(inventory.bp)
    app.register_blueprint(accounting.bp)
    app.register_blueprint(projects.projects_bp)
    app.register_blueprint(storage.storage_bp)
    app.register_blueprint(logistics.logistics_bp)
    app.register_blueprint(acceptance.acceptance_bp)
    app.register_blueprint(delivery_management.delivery_bp)
    app.register_blueprint(receiving.bp)
    app.register_blueprint(putaway.bp)
    
    # EMERGENCY FIX: Removed manual CORS handlers that were conflicting
    # Flask-CORS should handle all CORS needs without manual intervention
    print(f"[CORS] Manual CORS handlers removed to prevent conflicts")
    
    return app