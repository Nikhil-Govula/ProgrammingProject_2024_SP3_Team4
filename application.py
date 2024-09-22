from flask_mail import Mail
from flask import redirect, request
from src import create_app
from google_auth_oauthlib.flow import Flow
from config import CLIENT_SECRET, store_secret

import os
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

mail = Mail()

# Initialize OAuth 2.0 flow using the client secret
flow = Flow.from_client_config(
    CLIENT_SECRET,
    scopes=['https://www.googleapis.com/auth/gmail.send']
)
flow.redirect_uri = 'http://localhost:8080/oauth2callback'

def create_application():
    app = create_app()

    # OAuth routes
    @app.route('/authorize')
    def authorize():
        authorization_url, _ = flow.authorization_url(prompt='consent')
        return redirect(authorization_url)

    @app.route('/oauth2callback')
    def oauth2callback():
        flow.fetch_token(authorization_response=request.url)
        credentials = flow.credentials
        # Store these credentials in SSM Parameter Store
        store_secret('/your-app/token', credentials.to_json())
        return 'Authentication successful'

    return app

application = app = create_application()

if __name__ == '__main__':
    application.run(host='0.0.0.0', port=8080, debug=True)