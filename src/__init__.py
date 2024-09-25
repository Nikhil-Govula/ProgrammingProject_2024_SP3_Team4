from flask import Flask
from flask_mail import Mail
from config import Config
import os

# Initialize extensions without binding to app
mail = Mail()

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

    # Set environment variable for OAuth
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = app.config.get('OAUTHLIB_INSECURE_TRANSPORT', '1')

    # Initialize OAuth 2.0 flow
    from google_auth_oauthlib.flow import Flow
    flow = Flow.from_client_config(
        app.config['CLIENT_SECRET'],
        scopes=['https://www.googleapis.com/auth/gmail.send']
    )
    flow.redirect_uri = app.config.get('OAUTH_REDIRECT_URI', 'http://localhost:8080/oauth2callback')
    app.flow = flow  # Attach flow to app for access in views

    # Register blueprints
    from .views import index_bp, logins_bp, registers_bp
    app.register_blueprint(index_bp)
    app.register_blueprint(logins_bp)
    app.register_blueprint(registers_bp)

    # Additional setup (e.g., error handlers) can be added here

    return app
