import logging
from flask import Flask, request, g, render_template
from flask_mail import Mail
from google_auth_oauthlib.flow import Flow

from config import Config
import os

from .controllers.index_controller import get_user
from .services import SessionManager

from .views import index_bp, landing_bp, user_bp, employer_bp, admin_bp
# from .services.google_auth_service import GoogleAuthService

# Initialize extensions without binding to app
mail = Mail()

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

def create_app(config_class=Config):
    # Initialize configurations (load secrets from AWS SSM)
    config_class.init_app()

    app = Flask(__name__,
                template_folder=os.path.join(os.path.dirname(__file__), 'templates'),
                static_folder=os.path.join(os.path.dirname(__file__), 'static'))

    # Load configuration
    app.config.from_object(config_class)

    # Initialize extensions with app
    mail.init_app(app)

    # Middleware to load session
    @app.before_request
    def load_session():
        session_id = request.cookies.get('session_id')
        if session_id:
            session = SessionManager.get_session(session_id)
            if session:
                user_id = session.get('user_id')
                user_type = session.get('user_type')
                user = get_user(user_id, user_type)
                if user:
                    g.user = user
                    g.user_type = user_type
                    print(f"Session loaded for {user_type}: {user_id}")  # Debug log
                else:
                    g.user = None
                    g.user_type = None
                    print(f"User not found for session: {user_id}, {user_type}")  # Debug log
            else:
                g.user = None
                g.user_type = None
                print("No valid session found")  # Debug log
        else:
            g.user = None
            g.user_type = None
            print("No session ID in cookie")  # Debug log

    # Set environment variable for OAuth
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = app.config.get('OAUTHLIB_INSECURE_TRANSPORT', '1')

    # Initialize OAuth 2.0 flow
    flow = Flow.from_client_config(
        app.config['CLIENT_SECRET'],
        scopes=['https://www.googleapis.com/auth/gmail.send']
    )
    flow.redirect_uri = app.config.get('OAUTH_REDIRECT_URI', 'http://localhost:8080/user/oauth2callback')
    app.flow = flow  # Attach flow to app for access in views

    # Register blueprints
    app.register_blueprint(index_bp)
    app.register_blueprint(landing_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(employer_bp)
    app.register_blueprint(admin_bp)

    # Middleware to handle session expiration or refresh if needed
    @app.after_request
    def save_session(response):
        # Optionally, extend session expiration or perform other tasks
        return response

    # Register error handlers
    register_error_handlers(app)

    return app

def register_error_handlers(app):
    @app.errorhandler(404)
    def page_not_found(e):
        logging.error(f"404 Error: {e}")
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_error(e):
        logging.error(f"500 Error: {e}")
        return render_template('500.html'), 500
