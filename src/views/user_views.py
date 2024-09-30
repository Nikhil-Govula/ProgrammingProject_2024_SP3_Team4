import json

from flask import Blueprint, render_template, request, redirect, url_for, make_response, g, current_app, session
from google.auth.transport import requests
from google.oauth2.credentials import Credentials

from config import store_secret
from ..controllers import UserController
from ..decorators.auth_required import auth_required
from ..services import SessionManager
from ..services.google_auth_service import GoogleAuthService

user_bp = Blueprint('user_views', __name__, url_prefix='/user')

@user_bp.route('/login', methods=['GET', 'POST'])
def login_user():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user, error_message = UserController.login(email, password)
        if user:
            session_id = SessionManager.create_session(user.user_id, 'user')
            if session_id:
                response = make_response(redirect(url_for('user_views.dashboard')))
                response.set_cookie('session_id', session_id, httponly=True, secure=True, samesite='Lax')
                return response
            else:
                error = "Failed to create session. Please try again."
                return render_template('user/login_user.html', error=error)
        else:
            return render_template('user/login_user.html', error=error_message)
    return render_template('user/login_user.html')

@user_bp.route('/register', methods=['GET', 'POST'])
def register_user():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        phone_number = request.form['phone_number']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # Validate form inputs
        if password != confirm_password:
            error = "Passwords do not match!"
            return render_template('user/register_user.html', error=error)

        # Register the new user
        success, message = UserController.register_user(email, password, first_name, last_name, phone_number)
        if success:
            return redirect(url_for('user_views.login_user'))
        else:
            return render_template('user/register_user.html', error=message)

    return render_template('user/register_user.html')

@user_bp.route('/dashboard', methods=['GET'])
@auth_required()
def dashboard():
    user = g.user
    return render_template('user/dashboard.html', user=user)

@user_bp.route('/logout', methods=['GET'])
def logout():
    session_id = request.cookies.get('session_id')
    if session_id:
        SessionManager.delete_session(session_id)
    response = make_response(redirect(url_for('landing.landing')))
    response.set_cookie('session_id', '', expires=0)
    return response

# **New Routes for Reset Password**

@user_bp.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        email = request.form['email']
        success, message, was_locked = UserController.reset_password(email)
        return render_template('user/reset_password.html', success=success, message=message, was_locked=was_locked, email=email)
    return render_template('user/reset_password.html')

@user_bp.route('/reset/<token>', methods=['GET', 'POST'])
def reset_with_token(token):
    if request.method == 'POST':
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        if new_password != confirm_password:
            return render_template('user/reset_with_token.html', error="Passwords do not match", token=token)

        success, message, was_locked = UserController.reset_password_with_token(token, new_password)
        if success:
            return redirect(url_for('user_views.login_user', message=message))
        else:
            return render_template('user/reset_with_token.html', error=message, token=token)

    return render_template('user/reset_with_token.html', token=token)


# Test function for token refresh
@user_bp.route('/refresh_token', methods=['GET'])
def refresh_token():
    try:
        credentials = GoogleAuthService.get_credentials()
        if credentials is None:
            # Redirect to re-authentication
            return redirect(url_for('user_views.start_oauth_flow'))
        return f"Token refreshed successfully. New expiry: {credentials.expiry}", 200
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        return f"Error refreshing token: {str(e)}\n\nTraceback:\n{error_traceback}", 500


@user_bp.route('/setup_oauth')
def setup_oauth():
    return redirect(url_for('user_views.start_oauth_flow'))

@user_bp.route('/start_oauth_flow')
def start_oauth_flow():
    flow = current_app.flow  # Getting the flow from the app context
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'  # Force consent to receive a new refresh_token. Fewer token errors with this enabled
    )
    session['state'] = state  # Store state in the session
    return redirect(authorization_url)


@user_bp.route('/oauth2callback')
def oauth2callback():
    if 'state' not in session or session['state'] != request.args.get('state'):
        return 'Invalid state parameter', 400

    flow = current_app.flow  # Get flow from app context
    try:
        flow.fetch_token(authorization_response=request.url)
    except Exception as e:
        return f"Error during token fetching: {str(e)}", 400

    credentials = flow.credentials
    session['credentials'] = {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }

    # Store the credentials in AWS SSM
    store_secret('/your-app/token', json.dumps(session['credentials']))

    return redirect(url_for('user_views.dashboard'))

@user_bp.route('/revoke')
def revoke():
    if 'credentials' not in session:
        return 'You need to <a href="/start_oauth_flow">authorize</a> before revoking credentials.', 400

    credentials = Credentials(**session['credentials'])

    revoke = requests.post('https://oauth2.googleapis.com/revoke',
        params={'token': credentials.token},
        headers = {'content-type': 'application/x-www-form-urlencoded'})

    status_code = getattr(revoke, 'status_code', 500)
    if status_code == 200:
        return 'Credentials successfully revoked.'
    else:
        return 'An error occurred.'