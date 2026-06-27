import os
import redis
from flask import Flask, jsonify
from .config import config
from .extensions import db, migrate, jwt, ma, bcrypt, limiter, cors, mail
import app.extensions as ext


def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    ma.init_app(app)
    bcrypt.init_app(app)
    limiter.init_app(app)
    mail.init_app(app)
    cors.init_app(app, resources={r'/api/*': {'origins': app.config['CORS_ORIGINS']}})

    # Initialize Redis
    ext.redis_client = redis.from_url(
        app.config['REDIS_URL'],
        decode_responses=True
    )

    # JWT token blocklist
    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        jti = jwt_payload['jti']
        return ext.redis_client.get(f'blocklist:{jti}') is not None

    # JWT error handlers
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({'success': False, 'error': 'TOKEN_EXPIRED', 'message': 'Token has expired'}), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({'success': False, 'error': 'INVALID_TOKEN', 'message': 'Token is invalid'}), 401

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({'success': False, 'error': 'UNAUTHORIZED', 'message': 'Authentication required'}), 401

    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        return jsonify({'success': False, 'error': 'TOKEN_REVOKED', 'message': 'Token has been revoked'}), 401

    # Global error handlers
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({'success': False, 'error': 'NOT_FOUND', 'message': 'Resource not found'}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({'success': False, 'error': 'METHOD_NOT_ALLOWED', 'message': 'Method not allowed'}), 405

    @app.errorhandler(429)
    def rate_limit_exceeded(e):
        return jsonify({'success': False, 'error': 'RATE_LIMIT_EXCEEDED', 'message': str(e.description)}), 429

    @app.errorhandler(500)
    def internal_error(e):
        db.session.rollback()
        return jsonify({'success': False, 'error': 'INTERNAL_ERROR', 'message': 'An internal error occurred'}), 500

    # Register blueprints
    from .routes.auth import auth_bp
    from .routes.flights import flights_bp
    from .routes.bookings import bookings_bp
    from .routes.passengers import passengers_bp
    from .routes.crew import crew_bp
    from .routes.aircraft import aircraft_bp
    from .routes.airports import airports_bp
    from .routes.payments import payments_bp
    from .routes.reports import reports_bp
    from .routes.notifications import notifications_bp
    from .routes.users import users_bp

    app.register_blueprint(auth_bp, url_prefix='/api/v1/auth')
    app.register_blueprint(flights_bp, url_prefix='/api/v1/flights')
    app.register_blueprint(bookings_bp, url_prefix='/api/v1/bookings')
    app.register_blueprint(passengers_bp, url_prefix='/api/v1/passengers')
    app.register_blueprint(crew_bp, url_prefix='/api/v1/crew')
    app.register_blueprint(aircraft_bp, url_prefix='/api/v1/aircraft')
    app.register_blueprint(airports_bp, url_prefix='/api/v1/airports')
    app.register_blueprint(payments_bp, url_prefix='/api/v1/payments')
    app.register_blueprint(reports_bp, url_prefix='/api/v1/reports')
    app.register_blueprint(notifications_bp, url_prefix='/api/v1/notifications')
    app.register_blueprint(users_bp, url_prefix='/api/v1/users')

    # Health check
    @app.route('/api/v1/health')
    def health():
        return jsonify({'status': 'ok', 'service': 'flight-management-api'})

    return app
