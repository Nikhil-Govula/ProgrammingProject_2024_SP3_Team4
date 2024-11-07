import datetime
from datetime import datetime, timezone
from datetime import datetime as dt
import json
import uuid
import requests
import time

import boto3
from botocore.exceptions import ClientError
from flask import Blueprint, render_template, request, redirect, url_for, make_response, g, current_app, session, \
    jsonify, flash, Response, Flask
from google.auth.transport import requests as google_requests
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from werkzeug.utils import secure_filename

from config import store_secret, Config
from ..controllers import UserController
from ..decorators.auth_required import auth_required
from ..models import User, Employer, Message, Job
from ..services import SessionManager, DynamoDB
from ..services.google_auth_service import GoogleAuthService

user_bp = Blueprint('user_views', __name__, url_prefix='/user')


@user_bp.route('/login', methods=['GET', 'POST'])
def login_user():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user, error_message = UserController.login(email, password)
        if user:
            if not user.is_active:
                flash("Your account is not active. Please check your email to verify your account.", "error")
                return render_template('user/login_user.html')
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
            flash(message, 'success')  # Flash the success message
            return redirect(url_for('user_views.login_user'))
        else:
            flash(message, 'error')  # Optionally flash error message
            return render_template('user/register_user.html')

    return render_template('user/register_user.html')


@user_bp.route('/verify/<token>', methods=['GET', 'POST'])
def verify_account(token):
    if request.method == 'POST':
        success, message = User.verify_account(token)
        if success:
            flash("Your account has been verified successfully! You can now log in.", "success")
            return redirect(url_for('user_views.login_user'))
        else:
            flash(message, "error")
            return render_template('user/verify_account.html', token=token), 400
    else:
        # For GET requests, render the verification confirmation page
        return render_template('user/verify_account.html', token=token)

@user_bp.route('/dashboard', methods=['GET'])
@auth_required(user_type='user')
def dashboard():
    user = g.user
    recommended_jobs = UserController.get_recommended_jobs(user)
    return render_template('user/dashboard.html', user=user, jobs=recommended_jobs)


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
        return render_template('user/reset_password.html', success=success, message=message, was_locked=was_locked,
                               email=email)
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
    # Instantiate a new Flow object using the CLIENT_SECRET and redirect_uri from config
    flow = Flow.from_client_config(
        current_app.config['CLIENT_SECRET'],
        scopes=['https://www.googleapis.com/auth/gmail.send']
    )
    flow.redirect_uri = current_app.config['OAUTH_REDIRECT_URI']

    # Generate the authorization URL
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        # prompt='consent'  # Force consent to receive a new refresh_token
    )

    # Store the state in the session for validation in the callback
    session['state'] = state

    # Log the OAuth flow initiation
    current_app.logger.info(f"OAuth flow started with state: {state}")
    current_app.logger.info(f"Authorization URL: {authorization_url}")

    return redirect(authorization_url)


@user_bp.route('/oauth2callback')
def oauth2callback():
    # Validate the state parameter to prevent CSRF attacks
    state = session.get('state')
    incoming_state = request.args.get('state')
    if not state or state != incoming_state:
        current_app.logger.error("Invalid or missing state parameter in OAuth callback")
        return 'Invalid state parameter', 400

    # Instantiate a new Flow object using the CLIENT_SECRET and redirect_uri from config
    flow = Flow.from_client_config(
        current_app.config['CLIENT_SECRET'],
        scopes=['https://www.googleapis.com/auth/gmail.send']
    )
    flow.redirect_uri = current_app.config['OAUTH_REDIRECT_URI']

    # Complete the OAuth flow by fetching the token
    try:
        flow.fetch_token(authorization_response=request.url)
    except Exception as e:
        current_app.logger.error(f"Error during token fetching: {e}")
        return f"Error during token fetching: {str(e)}", 400

    # Retrieve the credentials from the flow
    credentials = flow.credentials

    # Store the credentials in the session
    session['credentials'] = {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }

    # Store the credentials securely in AWS SSM
    store_secret('/your-app/token', json.dumps(session['credentials']))
    current_app.logger.info("OAuth credentials successfully stored in AWS SSM")

    return redirect(url_for('user_views.dashboard'))


@user_bp.route('/revoke')
def revoke():
    if 'credentials' not in session:
        return 'You need to <a href="/start_oauth_flow">authorize</a> before revoking credentials.', 400

    credentials = Credentials(**session['credentials'])

    revoke = requests.post('https://oauth2.googleapis.com/revoke',
                           params={'token': credentials.token},
                           headers={'content-type': 'application/x-www-form-urlencoded'})

    status_code = getattr(revoke, 'status_code', 500)
    if status_code == 200:
        return 'Credentials successfully revoked.'
    else:
        return 'An error occurred.'


@user_bp.route('/profile', methods=['GET'])
@auth_required(user_type='user')
def view_profile():
    user = g.user
    return render_template('user/profile.html', user=user)


@user_bp.route('/profile/edit', methods=['GET', 'POST'])
@auth_required(user_type='user')
def edit_profile():
    user = g.user
    if request.method == 'POST':
        first_name = request.form.get('first_name').strip()
        last_name = request.form.get('last_name').strip()
        email = request.form.get('email').strip()
        phone_number = request.form.get('phone_number').strip()
        profile_picture = request.files.get('profile_picture')
        certifications = request.files.getlist('certifications')
        location = request.form.get('location').strip()

        success, message = UserController.update_profile(
            user_id=user.user_id,
            user_type='user',
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone_number=phone_number,
            profile_picture=profile_picture,
            certifications=certifications,
            location=location  # Ensure this parameter is now accepted
        )

        if success:
            return redirect(url_for('user_views.view_profile', success=message))
        else:
            return render_template('user/profile_edit.html', user=user, error=message)

    return render_template('user/profile_edit.html', user=user)


@user_bp.route('/upload_profile_picture', methods=['POST'])
@auth_required(user_type='user')
def upload_profile_picture():
    user = g.user
    if 'profile_picture' not in request.files:
        return jsonify({'success': False, 'message': 'No profile picture file in the request.'}), 400

    file = request.files['profile_picture']
    if file and UserController.allowed_image_file(file.filename):
        new_profile_picture_url, error = UserController.update_profile_picture(user, file)
        if error:
            return jsonify({'success': False, 'message': error}), 400
        user.profile_picture_url = new_profile_picture_url
        user.save()
        return jsonify({'success': True, 'profile_picture_url': new_profile_picture_url}), 200
    else:
        return jsonify({'success': False, 'message': 'Invalid file type for profile picture.'}), 400


@user_bp.route('/upload_certification', methods=['POST'])
@auth_required(user_type='user')
def upload_certification():
    user = g.user
    cert_file = request.files.get('certifications')
    cert_type = request.form.get('cert_type')

    # Validate presence of both file and certification type
    if not cert_file:
        return jsonify({'success': False, 'message': 'No certification file provided.'}), 400

    if not cert_type or cert_type.strip() == "":
        return jsonify({'success': False, 'message': 'Certification type is required.'}), 400

    if not UserController.allowed_certification_file(cert_file.filename):
        return jsonify({'success': False, 'message': 'Invalid file type for certification.'}), 400

    cert_type = cert_type.strip()

    # Upload the certification
    cert_url, original_filename, cert_id, error = UserController.upload_certification(user, cert_file, cert_type)

    if error:
        return jsonify({'success': False, 'message': error}), 400

    # Return the newly added certification details
    return jsonify({
        'success': True,
        'certifications': [{
            'id': cert_id,
            'url': cert_url,
            'filename': original_filename,
            'type': cert_type
        }]
    }), 200


@user_bp.route('/delete_certification', methods=['POST'])
@auth_required(user_type='user')
def delete_certification():
    user = g.user
    data = request.get_json()
    cert_id = data.get('cert_id')

    if not cert_id:
        return jsonify({'success': False, 'message': 'No certification ID provided.'}), 400

    cert_to_delete = next((cert for cert in user.certifications if cert.get('id') == cert_id), None)
    if not cert_to_delete:
        return jsonify({'success': False, 'message': 'Certification not found.'}), 404

    # Remove from S3
    success = UserController.delete_certification(user.user_id, cert_to_delete['url'])
    if not success:
        return jsonify({'success': False, 'message': 'Failed to delete certification from storage.'}), 500

    # Remove from user certifications
    user.certifications = [cert for cert in user.certifications if cert.get('id') != cert_id]
    user.save()

    return jsonify({'success': True, 'message': 'Certification deleted successfully.'}), 200


@user_bp.route('/update_field', methods=['POST'])
@auth_required(user_type='user')
def update_profile_field():
    data = request.get_json()
    field = data.get('field')
    value = data.get('value')

    if not field or value is None:
        return jsonify({'success': False, 'message': 'Invalid request parameters.'}), 400

    allowed_fields = {'first_name', 'last_name', 'email', 'phone_number', 'location'}
    if field not in allowed_fields:
        return jsonify({'success': False, 'message': 'Field not allowed to update.'}), 400

    user = g.user

    # Update the field using the UserController
    success, message = UserController.update_profile_field(user.user_id, field, value)

    if success:
        return jsonify({'success': True, 'message': message}), 200
    else:
        return jsonify({'success': False, 'message': message}), 400


@user_bp.route('/change_password', methods=['GET', 'POST'])
@auth_required(user_type='user')
def change_password():
    user = g.user
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        success, message = UserController.change_password(
            user_id=user.user_id,
            current_password=current_password,
            new_password=new_password,
            confirm_password=confirm_password
        )

        if success:
            return redirect(url_for('user_views.view_profile', success=message))
        else:
            return render_template('user/change_password.html', error=message)

    return render_template('user/change_password.html')


@user_bp.route('/city_suggestions', methods=['GET'])
def city_suggestions():
    query = request.args.get('query', '').strip()
    if not query:
        return jsonify({'suggestions': []}), 200

    api_gateway_url = 'https://w6z5elzk0b.execute-api.ap-southeast-2.amazonaws.com/city'

    try:
        response = requests.get(api_gateway_url, params={'query': query}, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return jsonify({'suggestions': data['suggestions']}), 200
        else:
            current_app.logger.error(f"API Gateway error: {response.status_code} - {response.text}")
            return jsonify({'suggestions': []}), 200
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Error calling CitySuggestionsAPI: {e}")
        return jsonify({'suggestions': []}), 200


@user_bp.route('/work_history', methods=['GET'])
@auth_required(user_type='user')
def view_work_history():
    user = g.user

    # Sort work history by 'date_from' in descending order (most recent first)
    sorted_work_history = sorted(
        user.work_history,
        key=lambda x: x.get('date_to', ''),
        reverse=True  # Set to False for ascending order
    )

    return render_template('user/work_history.html', user=user, work_history=sorted_work_history)


@user_bp.route('/add_work_history', methods=['POST'])
@auth_required(user_type='user')
def add_work_history():
    data = request.get_json()
    job_title = data.get('job_title')
    company = data.get('company')
    description = data.get('description', '')
    date_from = data.get('date_from')
    date_to = data.get('date_to', '')

    success, message = UserController.add_work_history(
        user_id=g.user.user_id,
        job_title=job_title,
        company=company,
        description=description,
        date_from=date_from,
        date_to=date_to
    )

    if success:
        # Refresh the user object to get the updated work history
        updated_user = UserController.get_user_by_id(g.user.user_id)
        if updated_user and updated_user.work_history:
            latest_work = updated_user.work_history[-1]
            return jsonify({'success': True, 'work_history': latest_work}), 200
        else:
            return jsonify({'success': False, 'message': 'Work history added but unable to retrieve it.'}), 500
    else:
        return jsonify({'success': False, 'message': message}), 400


@user_bp.route('/delete_work_history', methods=['POST'])
@auth_required(user_type='user')
def delete_work_history():
    data = request.get_json()
    work_id = data.get('work_id')

    if not work_id:
        return jsonify({'success': False, 'message': 'No work history ID provided.'}), 400

    success, message = UserController.delete_work_history(
        user_id=g.user.user_id,
        work_id=work_id
    )

    if success:
        return jsonify({'success': True, 'message': message}), 200
    else:
        return jsonify({'success': False, 'message': message}), 400


@user_bp.route('/get_occupation_suggestions', methods=['GET'])
def get_occupation_suggestions():
    query = request.args.get('query', '').strip().lower()
    if not query:
        return jsonify({'suggestions': []}), 200

    api_gateway_url = 'https://w6z5elzk0b.execute-api.ap-southeast-2.amazonaws.com/occupation'

    try:
        response = requests.get(api_gateway_url, params={'query': query}, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return jsonify({'suggestions': data.get('suggestions', [])}), 200
        else:
            current_app.logger.error(f"Occupation API error: {response.status_code} - {response.text}")
            return jsonify({'suggestions': []}), 200
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Error calling OccupationAutocompleteAPI: {e}")
        return jsonify({'suggestions': []}), 200


@user_bp.route('/certification_suggestions', methods=['GET'])
def certification_suggestions():
    query = request.args.get('query', '').strip()
    if not query:
        return jsonify({'suggestions': []}), 200

    api_gateway_url = 'https://w6z5elzk0b.execute-api.ap-southeast-2.amazonaws.com/certification'

    try:
        response = requests.get(api_gateway_url, params={'query': query}, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return jsonify({'suggestions': data.get('suggestions', [])}), 200
        else:
            current_app.logger.error(f"Certification API error: {response.status_code} - {response.text}")
            return jsonify({'suggestions': []}), 200
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Error calling CertificationAutocompleteAPI: {e}")
        return jsonify({'suggestions': []}), 200


@user_bp.route('/skills', methods=['GET'])
@auth_required(user_type='user')
def view_skills():
    user = g.user
    return render_template('user/skills.html', user=user)


@user_bp.route('/add_skill', methods=['POST'])
@auth_required(user_type='user')
def add_skill():
    user = g.user
    data = request.get_json()
    skill_text = data.get('skill')

    success, skill_data, error = UserController.add_skill(user.user_id, skill_text)

    if success:
        return jsonify({'success': True, 'skill': skill_data}), 200
    else:
        return jsonify({'success': False, 'message': error}), 400


@user_bp.route('/delete_skill', methods=['POST'])
@auth_required(user_type='user')
def delete_skill():
    user = g.user
    data = request.get_json()
    skill_id = data.get('skill_id')

    success, message, error = UserController.delete_skill(user.user_id, skill_id)

    if success:
        return jsonify({'success': True, 'message': message}), 200
    else:
        return jsonify({'success': False, 'message': message}), 400


@user_bp.route('/skill_suggestions', methods=['GET'])
def skill_suggestions():
    query = request.args.get('query', '').strip()
    if not query:
        return jsonify({'suggestions': []}), 200

    api_gateway_url = 'https://w6z5elzk0b.execute-api.ap-southeast-2.amazonaws.com/skill'

    try:
        response = requests.get(api_gateway_url, params={'query': query}, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return jsonify({'suggestions': data.get('suggestions', [])}), 200
        else:
            current_app.logger.error(f"Skill API error: {response.status_code} - {response.text}")
            return jsonify({'suggestions': []}), 200
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Error calling SkillAutocompleteAPI: {e}")
        return jsonify({'suggestions': []}), 200


# src/views/user_views.py


@user_bp.route('/jobs', methods=['GET'])
@auth_required(user_type='user')
def view_all_jobs():
    """
    Render a page displaying all available jobs with pagination.
    """
    page = int(request.args.get('page', 1))
    per_page = 10  # Number of jobs per page
    jobs = UserController.get_all_active_jobs()

    total_jobs = len(jobs)
    total_pages = (total_jobs + per_page - 1) // per_page
    start = (page - 1) * per_page
    end = start + per_page
    paginated_jobs = jobs[start:end]

    return render_template(
        'user/view_jobs.html',
        jobs=paginated_jobs,
        page=page,
        total_pages=total_pages
    )


@user_bp.route('/job_details/<job_id>', methods=['GET'])
@auth_required(user_type='user')
def get_job_details(job_id):
    job = UserController.get_job_by_id(job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404

    user_id = g.user.user_id
    has_applied = UserController.has_applied_for_job(user_id, job_id)

    return jsonify({
        "job_id": job.job_id,
        "job_title": job.job_title,
        "company_name": job.company_name,
        "city": job.city,
        "country": job.country,
        "salary": f"{job.salary:,.2f}",
        "date_posted": job.date_posted,
        "description": job.description,
        "requirements": job.requirements,
        "certifications": job.certifications or [],
        "skills": job.skills or [],
        "has_applied": has_applied  # Include application status
    })


@user_bp.route('/jobs/<job_id>', methods=['GET'])
@auth_required(user_type='user')
def view_job_details(job_id):
    job = UserController.get_job_by_id(job_id)
    if not job:
        flash("Job not found or is no longer available.", 'error')
        return redirect(url_for('user_views.view_all_jobs'))

    user_id = g.user.user_id
    print(f"Checking application status for user {user_id} and job {job_id}")

    # Get the application if it exists
    application = UserController.get_application(user_id, job_id)
    has_applied = application is not None

    return render_template('user/job_detail.html',
                           job=job,
                           has_applied=has_applied,
                           application=application)


@user_bp.route('/jobs/<job_id>/bookmark', methods=['POST'])
@auth_required(user_type='user')
def bookmark_job(job_id):
    print("bookmark_job")
    user = g.user
    success, message = UserController.save_job(user.user_id, job_id)
    if success:
        return '', 200
    else:
        return jsonify({'error': message}), 400


@user_bp.route('/jobs/<job_id>/remove_bookmark', methods=['POST'])
@auth_required(user_type='user')
def remove_bookmark_job(job_id):
    print("remove_bookmark_job")
    user = g.user
    success, message = UserController.remove_saved_job(user.user_id, job_id)
    if success:
        return '', 200
    else:
        return jsonify({'error': message}), 400


@user_bp.route('/get_bookmarked_jobs', methods=['GET'])
@auth_required(user_type='user')
def get_bookmarked_jobs():
    user = g.user
    bookmarked_jobs = user.saved_jobs  # Assuming `saved_jobs` is a list of job IDs saved by the user
    return jsonify({'bookmarkedJobs': bookmarked_jobs}), 200


@user_bp.route('/jobs/<job_id>/apply', methods=['POST'])
@auth_required(user_type='user')
def apply_for_job(job_id):
    user = g.user

    if UserController.has_applied_for_job(user.user_id, job_id):
        return jsonify({
            'success': False,
            'message': 'You have already applied for this position.'
        }), 400

    success, message = UserController.apply_for_job(user.user_id, job_id)
    print(f"apply JobID:\n{job_id}")

    response_data = {
        'success': success,
        'message': message,
        'reload': False  # No need for full reload, just update the status
    }

    return jsonify(response_data), 200 if success else 400


@user_bp.route('/jobs/<job_id>/revoke', methods=['POST'])
@auth_required(user_type='user')
def revoke_application(job_id):
    user = g.user
    success, message = UserController.revoke_application(user.user_id, job_id)
    print(f"revoke JobID:\n{job_id}")

    response_data = {
        'success': success,
        'message': message,
    }

    return jsonify(response_data), 200 if success else 400
# **New Routes for Recommended Jobs, Saved Jobs, Applications, and Resources**


@user_bp.route('/recommended_jobs', methods=['GET'])
@auth_required(user_type='user')
def recommended_jobs():
    user = g.user
    recommended_jobs = UserController.get_recommended_jobs(user)
    print(f"Recommended Jobs for user {user.user_id}: {recommended_jobs}")
    return render_template('user/recommended_jobs.html', jobs=recommended_jobs)


@user_bp.route('/saved_jobs', methods=['GET'])
@auth_required(user_type='user')
def saved_jobs():
    user = g.user
    saved_jobs = UserController.get_saved_jobs(user.user_id)
    return render_template('user/saved_jobs.html', jobs=saved_jobs)


@user_bp.route('/view_applications', methods=['GET'])
@auth_required(user_type='user')
def view_applications():
    user = g.user
    applications = UserController.get_user_applications(user.user_id)
    return render_template('user/view_applications.html', applications=applications)


@user_bp.route('/interview_tips', methods=['GET'])
@auth_required(user_type='user')
def interview_tips():
    tips = UserController.get_interview_tips()
    return render_template('user/interview_tips.html', tips=tips)


@user_bp.route('/networking_events', methods=['GET'])
@auth_required(user_type='user')
def networking_events():
    events = UserController.get_networking_events()
    return render_template('user/networking_events.html', events=events)


@user_bp.route('/messages/<employer_id>', methods=['GET', 'POST'])
@auth_required(user_type='user')
def chat_with_employer(employer_id):
    job_id = request.args.get('job_id')
    employer = Employer.get_by_id(employer_id)
    job = Job.get_by_id(job_id) if job_id else None

    if not employer:
        flash("Employer not found", "error")
        return redirect(url_for('user_views.view_all_chats'))

    if request.method == 'POST':
        content = request.json.get('content')
        if not content:
            return jsonify({'success': False, 'message': 'Message content required'}), 400

        message = Message(
            sender_id=g.user.user_id,
            receiver_id=employer_id,
            sender_type='user',
            content=content,
            job_id=job_id
        )
        message.save()
        return jsonify({
            'success': True,
            'message': {
                'message_id': message.message_id,  # Add this line
                'content': message.content,
                'timestamp': message.timestamp,
                'sender_type': message.sender_type
            }
        })

    # Mark all messages in this conversation as read
    messages = Message.get_conversation(g.user.user_id, employer_id, job_id)
    for message in messages:
        if message.receiver_id == g.user.user_id and not message.is_read:
            message.mark_as_read()

    return render_template(
        'user/chat.html',
        messages=messages,
        employer=employer,
        job=job,
        job_id=job_id
    )


@user_bp.route('/messages', methods=['GET'])
@auth_required(user_type='user')
def view_all_chats():
    user_id = g.user.user_id

    # Get all messages for this user
    response = DynamoDB.scan(
        'Messages',
        FilterExpression='sender_id = :user_id OR receiver_id = :user_id',
        ExpressionAttributeValues={':user_id': user_id}
    )

    messages = response.get('Items', [])

    # Create a dictionary to store the latest message for each conversation
    conversations = {}
    for msg in messages:
        message = Message(**msg)
        other_id = message.receiver_id if message.sender_id == user_id else message.sender_id

        # Create a unique key combining employer_id and job_id
        conversation_key = f"{other_id}_{message.job_id}"

        if (conversation_key not in conversations or
                message.timestamp > conversations[conversation_key]['latest_message'].timestamp):
            # Get the employer information
            employer = Employer.get_by_id(other_id)
            # Get the job information
            job = Job.get_by_id(message.job_id) if message.job_id else None

            if employer:
                conversations[conversation_key] = {
                    'employer': employer,
                    'latest_message': message,
                    'unread_count': 0,
                    'job_id': message.job_id,
                    'job_title': job.job_title if job else 'General Discussion'
                }

    # Count unread messages for each conversation
    for conv_key in conversations:
        employer_id = conv_key.split('_')[0]
        job_id = conversations[conv_key]['job_id']

        unread_count = DynamoDB.scan(
            'Messages',
            FilterExpression=('sender_id = :other_id AND receiver_id = :user_id '
                            'AND is_read = :is_read AND job_id = :job_id'),
            ExpressionAttributeValues={
                ':other_id': employer_id,
                ':user_id': user_id,
                ':is_read': False,
                ':job_id': job_id
            }
        )
        conversations[conv_key]['unread_count'] = len(unread_count.get('Items', []))

    # Sort conversations by latest message timestamp
    sorted_conversations = sorted(
        conversations.values(),
        key=lambda x: x['latest_message'].timestamp,
        reverse=True
    )

    return render_template('user/messages.html', conversations=sorted_conversations)


@user_bp.route('/messages/stream')
@auth_required(user_type='user')
def stream_messages():
    from flask import copy_current_request_context, current_app

    user_id = g.user.user_id
    app = current_app._get_current_object()

    @copy_current_request_context
    def generate():
        last_check = dt.now(timezone.utc).isoformat()
        sent_message_ids = set()  # Track sent message IDs

        try:
            while True:
                with app.app_context():
                    try:
                        new_messages = Message.get_new_messages(user_id, last_check, user_type='user')

                        if new_messages:
                            for message in new_messages:
                                # Only send message if we haven't sent it before
                                if message.message_id not in sent_message_ids:
                                    sent_message_ids.add(message.message_id)
                                    data = {
                                        'message_id': message.message_id,  # Include message ID
                                        'content': message.content,
                                        'timestamp': message.timestamp,
                                        'sender_type': message.sender_type,
                                        'sender_id': message.sender_id,
                                        'receiver_id': message.receiver_id,
                                        'job_id': message.job_id,
                                        'conversation_id': f'{message.sender_id}_{message.job_id}'
                                    }
                                    yield f"data: {json.dumps(data)}\n\n"

                        last_check = dt.now(timezone.utc).isoformat()

                    except Exception as e:
                        app.logger.error(f"Stream error: {str(e)}")
                        yield f"data: {json.dumps({'error': str(e)})}\n\n"
                        return

                time.sleep(2)

        except GeneratorExit:
            pass

    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no'
        }
    )