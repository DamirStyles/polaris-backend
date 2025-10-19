"""
Polaris - Tech Career Path Navigator
Flask application for AI-powered career guidance

Helps users explore technology career paths through personalized 
role recommendations, skills mapping, and AI-generated insights.
"""

import os
import logging
from pathlib import Path
from flask import Flask, jsonify
from flask_cors import CORS

from config import config, validate_config
from career_advisor import LLMCareerAnalyzer
from routes import api


def create_app(config_name=None):
    """
    Create and configure Flask application.
    
    Args:
        config_name: Configuration environment ('development', 'production', 'testing')
    
    Returns:
        Flask: Configured Flask application instance
    """
    app = Flask(__name__)
    
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    config_errors = validate_config()
    if config_errors:
        raise RuntimeError(f"Configuration errors: {'; '.join(config_errors)}")
    
    config_class = config[config_name]
    app.config.from_object(config_class)
    config_class.init_app(app)
    
    setup_logging(app, config_class)
    initialize_analyzers(app)
    
    if app.config.get('CORS_ENABLED', True):
        CORS(app, origins=app.config.get('CORS_ORIGINS', '*'))
    
    app.register_blueprint(api)
    register_health_routes(app)
    register_error_handlers(app)
    
    app.logger.info(f'Polaris Career Path Navigator initialized ({config_name})')
    return app


def setup_logging(app, config_class):
    """Configure application logging."""
    logging.basicConfig(
        level=getattr(logging, config_class.LOG_LEVEL),
        format=config_class.LOG_FORMAT
    )


def initialize_analyzers(app):
    """Initialize LLM analyzer and role database with pre-calculated overlaps."""
    try:
        llm_analyzer = LLMCareerAnalyzer()
        app.config['LLM_ANALYZER'] = llm_analyzer
        app.logger.info('LLMCareerAnalyzer initialized')
        
        from routes import init_role_database
        init_role_database()
        app.logger.info('Role database and overlaps initialized')
        
    except Exception as e:
        app.logger.error(f'Analyzer initialization failed: {e}')
        raise


def register_health_routes(app):
    """Register health check endpoints for monitoring."""
    
    @app.route('/health')
    def health_check():
        """Simple health check endpoint"""
        return jsonify({'status': 'healthy'})
    
    @app.route('/health/detailed')
    def detailed_health():
        """Detailed health check with component status"""
        health = {'status': 'healthy', 'components': {}}
        
        try:
            app.config['LLM_ANALYZER']
            health['components']['llm_analyzer'] = {'status': 'healthy'}
        except Exception as e:
            health['components']['llm_analyzer'] = {'status': 'unhealthy', 'error': str(e)}
            health['status'] = 'degraded'
        
        try:
            from routes import get_role_database
            db = get_role_database()
            health['components']['role_database'] = {
                'status': 'healthy',
                'roles_count': len(db.all_roles)
            }
        except Exception as e:
            health['components']['role_database'] = {'status': 'unhealthy', 'error': str(e)}
            health['status'] = 'degraded'
        
        status_code = 200 if health['status'] == 'healthy' else 503
        return jsonify(health), status_code


def register_error_handlers(app):
    """Register global error handlers."""
    
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 Not Found errors"""
        return jsonify({'error': 'Not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 Internal Server errors"""
        app.logger.error(f'Internal error: {error}')
        return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=app.config['DEBUG'])