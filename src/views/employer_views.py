# src/views/employer_views.py
import json
import logging
import time
from datetime import timezone
from datetime import datetime as dt

from flask import Blueprint, render_template, request, redirect, url_for, make_response, g, flash, jsonify, Response, \
    Flask

from config import Config
from ..controllers import EmployerController
from ..decorators.auth_required import auth_required
from ..services import SessionManager, DynamoDB
from ..models import Job, Application, Employer, User, Message

employer_bp = Blueprint('employer_views', __name__, url_prefix='/employer')

@employer_bp.route('/login', methods=['GET', 'POST'])
def login_employer():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        employer, error_message = EmployerController.login(email, password)
        if employer:
            session_id = SessionManager.create_session(employer.employer_id, 'employer')
            if session_id:
                print(f"Employer logged in successfully: {employer.employer_id}")  # Debug log
                response = make_response(redirect(url_for('employer_views.dashboard')))
                response.set_cookie('session_id', session_id, httponly=True, secure=True, samesite='Lax')
                return response
            else:
                error = "Failed to create session. Please try again."
                return render_template('employer/login_employer.html', error=error)
        else:
            return render_template('employer/login_employer.html', error=error_message)
    return render_template('employer/login_employer.html')

@employer_bp.route('/register', methods=['GET', 'POST'])
def register_employer():
    if request.method == 'POST':
        company_name = request.form['company_name']
        contact_person = request.form['contact_person']
        email = request.form['email']
        phone_number = request.form['phone_number']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # Validate form inputs
        if password != confirm_password:
            error = "Passwords do not match!"
            return render_template('employer/register_employer.html', error=error)

        # Register the new employer
        success, message = EmployerController.register_employer(email, password, company_name, contact_person, phone_number)
        if success:
            flash(message, 'success')
            return redirect(url_for('employer_views.login_employer'))
        else:
            return render_template('employer/register_employer.html', error=message)

    return render_template('employer/register_employer.html')

@employer_bp.route('/verify/<token>', methods=['GET', 'POST'])
def verify_account(token):
    if request.method == 'POST':
        logging.info(f"Attempting to verify employer account with token: {token}")
        success, message = Employer.verify_account(token)
        if success:
            logging.info(f"Employer account verified successfully for token: {token}")
            flash("Your account has been verified successfully! You can now log in.", "success")
            return redirect(url_for('employer_views.login_employer'))
        else:
            logging.warning(f"Failed to verify employer account with token: {token} - Reason: {message}")
            flash(message, "error")
            return render_template('employer/verify_account.html', token=token, success=False), 400
    else:
        logging.info(f"Rendering verification page for employer with token: {token}")
        return render_template('employer/verify_account.html', token=token, success=False)


@employer_bp.route('/dashboard', methods=['GET'])
@auth_required(user_type='employer')
def dashboard():
    employer_id = g.user.employer_id
    all_jobs = EmployerController.list_employer_jobs(employer_id)
    return render_template('employer/dashboard.html', jobs=all_jobs)

@employer_bp.route('/logout', methods=['GET'])
def logout():
    session_id = request.cookies.get('session_id')
    if session_id:
        SessionManager.delete_session(session_id)
    response = make_response(redirect(url_for('landing.landing')))
    response.set_cookie('session_id', '', expires=0)
    return response

# **New Routes for Password Reset**

@employer_bp.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        email = request.form['email']
        success, message, was_locked = EmployerController.reset_password(email)
        return render_template('employer/reset_password.html', success=success, message=message, was_locked=was_locked, email=email)
    return render_template('employer/reset_password.html')

@employer_bp.route('/reset/<token>', methods=['GET', 'POST'])
def reset_with_token(token):
    if request.method == 'POST':
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        if new_password != confirm_password:
            return render_template('employer/reset_with_token.html', error="Passwords do not match", token=token)

        success, message, was_locked = EmployerController.reset_password_with_token(token, new_password)
        if success:
            flash(message, 'success')
            return redirect(url_for('employer_views.login_employer'))
        else:
            return render_template('employer/reset_with_token.html', error=message, token=token)

    return render_template('employer/reset_with_token.html', token=token)

JOBS_PER_PAGE = 10  # Define how many jobs to display per page

@employer_bp.route('/jobs/create', methods=['GET', 'POST'])
@auth_required(user_type='employer')
def create_job():
    if request.method == 'POST':
        data = request.get_json()
        job_title = data.get('job_title')
        description = data.get('description')
        requirements = data.get('requirements')
        salary = data.get('salary')
        location = data.get('city')
        certifications = data.get('certifications', [])
        skills = data.get('skills', [])
        work_history = data.get('work_history', [])
        company_name = g.user.company_name

        # Split location into city and country
        try:
            city, country = map(str.strip, location.split(',', 1))
            print(f"City: {city}, Country: {country}")  # Log parsed values
        except ValueError:
            return jsonify({'success': False, 'message': "Invalid location format. Please use 'City, Country'."}), 400

        # Convert work_history into list of dicts
        processed_work_history = []
        for entry in work_history:
            occupation = entry.get('occupation')
            duration = entry.get('duration')
            if occupation and duration:
                processed_work_history.append({
                    'occupation': occupation,
                    'duration': int(duration)
                })

        success, message = EmployerController.create_job(
            employer_id=g.user.employer_id,
            job_title=job_title,
            description=description,
            requirements=requirements,
            salary=salary,
            city=city,
            country=country,
            certifications=certifications,
            skills=skills,
            work_history=processed_work_history,
            company_name=company_name
        )

        if success:
            return jsonify({'success': True, 'message': message}), 200
        else:
            return jsonify({'success': False, 'message': message}), 400

    return render_template('employer/create_job.html')

@employer_bp.route('/jobs/edit/<job_id>', methods=['GET', 'POST'])
@auth_required(user_type='employer')
def edit_job(job_id):
    job = Job.get_by_id(job_id)
    if not job or job.employer_id != g.user.employer_id:
        if request.method == 'POST' and request.is_json:
            return jsonify({'success': False, 'message': "Job not found or unauthorized."}), 404
        flash("Job not found or you don't have permission to edit this job.", 'error')
        return redirect(url_for('employer_views.dashboard'))

    if request.method == 'POST':
        if request.is_json:
            # Handle AJAX JSON request for individual field updates
            data = request.get_json()
            fields = {}
            allowed_fields = ['job_title', 'description', 'requirements', 'salary', 'city', 'work_history']
            for key in allowed_fields:
                if key in data:
                    fields[key] = data[key]

            if not fields:
                return jsonify({'success': False, 'message': "No valid fields to update."}), 400

            success, message = EmployerController.update_job(job_id, fields)
            if success:
                return jsonify({'success': True, 'message': message}), 200
            else:
                return jsonify({'success': False, 'message': message}), 400
        else:
            # Handle standard form submission (if you decide to keep it)
            fields = {
                'job_title': request.form.get('job_title'),
                'description': request.form.get('description'),
                'requirements': request.form.get('requirements'),
                'salary': request.form.get('salary'),
                'city': request.form.get('city'),
                'work_history': request.form.get('work_history')
            }

            success, message = EmployerController.update_job(job_id, fields)
            if success:
                flash(message, 'success')
                return redirect(url_for('employer_views.dashboard'))
            else:
                flash(message, 'error')
                return render_template('employer/edit_job.html', job=job)

    # Handle GET request to render the edit_job.html template
    return render_template('employer/edit_job.html', job=job)

@employer_bp.route('/jobs/<job_id>/add_skill', methods=['POST'])
@auth_required(user_type='employer')
def add_job_skill(job_id):
    data = request.get_json()
    skill = data.get('skill')

    success, message = EmployerController.add_job_skill(job_id, skill)
    if success:
        return jsonify({'success': True, 'message': message}), 200
    else:
        return jsonify({'success': False, 'message': message}), 400  # Ensure message is included

@employer_bp.route('/jobs/<job_id>/delete_skill', methods=['POST'])
@auth_required(user_type='employer')
def delete_job_skill(job_id):
    data = request.get_json()
    skill = data.get('skill')

    success, message = EmployerController.remove_job_skill(job_id, skill)
    if success:
        return jsonify({'success': True, 'message': message}), 200
    else:
        return jsonify({'success': False, 'message': message}), 400

@employer_bp.route('/jobs/<job_id>/add_certification', methods=['POST'])
@auth_required(user_type='employer')
def add_job_certification(job_id):
    data = request.get_json()
    certification = data.get('certification')

    success, result = EmployerController.add_job_certification(job_id, certification)
    if success:
        return jsonify({'success': True, 'message': 'Certification added successfully', 'certification': result}), 200
    else:
        return jsonify({'success': False, 'message': result}), 400

@employer_bp.route('/jobs/<job_id>/delete_certification', methods=['POST'])
@auth_required(user_type='employer')
def delete_job_certification(job_id):
    data = request.get_json()
    certification = data.get('certification')

    success, message = EmployerController.remove_job_certification(job_id, certification)
    if success:
        return jsonify({'success': True, 'message': message}), 200
    else:
        return jsonify({'success': False, 'message': message}), 400

# **New Routes for Work History**

@employer_bp.route('/jobs/<job_id>/add_work_history', methods=['POST'])
@auth_required(user_type='employer')
def add_work_history(job_id):
    data = request.get_json()
    occupation = data.get('occupation')
    duration = data.get('duration')

    # Validate input
    if not occupation or not duration:
        return jsonify({'success': False, 'message': 'Occupation and duration are required.'}), 400

    try:
        duration = int(duration)
        if duration <= 0:
            raise ValueError
    except ValueError:
        return jsonify({'success': False, 'message': 'Duration must be a positive integer representing months.'}), 400

    success, message = EmployerController.add_job_work_history(job_id, occupation, duration)
    if success:
        return jsonify({'success': True, 'message': message, 'occupation': occupation, 'duration': duration}), 200
    else:
        return jsonify({'success': False, 'message': message}), 400

@employer_bp.route('/jobs/<job_id>/delete_work_history', methods=['POST'])
@auth_required(user_type='employer')
def delete_work_history(job_id):
    data = request.get_json()
    occupation = data.get('occupation')
    duration = data.get('duration')

    # Validate input
    if not occupation or not duration:
        return jsonify({'success': False, 'message': 'Occupation and duration are required.'}), 400

    try:
        duration = int(duration)
        if duration <= 0:
            raise ValueError
    except ValueError:
        return jsonify({'success': False, 'message': 'Duration must be a positive integer representing months.'}), 400

    success, message = EmployerController.remove_job_work_history(job_id, occupation, duration)
    if success:
        return jsonify({'success': True, 'message': message, 'occupation': occupation, 'duration': duration}), 200
    else:
        return jsonify({'success': False, 'message': message}), 400

@employer_bp.route('/jobs/delete/<job_id>', methods=['POST'])
@auth_required(user_type='employer')
def delete_job(job_id):
    success, message = EmployerController.delete_job(job_id)
    if success:
        return jsonify({'success': True, 'message': message}), 200
    else:
        return jsonify({'success': False, 'message': message}), 400


@employer_bp.route('/jobs/<job_id>/applications', methods=['GET'])
@auth_required(user_type='employer')
def view_job_applications(job_id):
    job = Job.get_by_id(job_id)
    if not job:
        flash("Job not found", 'error')
        return redirect(url_for('employer_views.dashboard'))

    if job.employer_id != g.user.employer_id:
        flash("You don't have permission to view these applications", 'error')
        return redirect(url_for('employer_views.dashboard'))

    applications = job.get_applications()
    return render_template('employer/view_applications.html',
                           applications=applications,
                           job=job)


@employer_bp.route('/jobs/applications/<application_id>/update-status', methods=['POST'])
@auth_required(user_type='employer')
def update_application_status(application_id):  # Add application_id parameter here
    data = request.get_json()
    new_status = data.get('status')

    # Get the application
    application = Application.get_by_id(application_id)
    if not application:
        return jsonify({
            'success': False,
            'message': 'Application not found'
        }), 404

    # Verify the employer owns the job
    job = Job.get_by_id(application.job_id)
    if not job or job.employer_id != g.user.employer_id:
        return jsonify({
            'success': False,
            'message': 'Unauthorized'
        }), 403

    # Update the status
    success = Application.update_status(application_id, new_status)

    return jsonify({
        'success': success,
        'message': 'Status updated successfully' if success else 'Failed to update status'
    })


@employer_bp.route('/messages/<user_id>', methods=['GET', 'POST'])
@auth_required(user_type='employer')
def chat_with_user(user_id):
    job_id = request.args.get('job_id')
    employer_id = g.user.employer_id  # Ensure you have access to the employer's ID
    user = User.get_by_id(user_id)
    job = Job.get_by_id(job_id) if job_id else None

    if not user:
        flash("User not found", "error")
        return redirect(url_for('employer_views.dashboard'))

    if request.method == 'POST':
        content = request.json.get('content')
        if not content:
            return jsonify({'success': False, 'message': 'Message content required'}), 400

        message = Message(
            sender_id=employer_id,
            receiver_id=user_id,
            sender_type='employer',
            content=content,
            job_id=job_id
        )
        message.save()
        return jsonify({
            'success': True,
            'message': {
                'message_id': message.message_id,
                'content': message.content,
                'timestamp': message.timestamp,
                'sender_type': message.sender_type
            }
        })

    # Retrieve the conversation
    messages = Message.get_conversation(user_id, employer_id, job_id)

    # Mark all received messages in this conversation as read
    for message in messages:
        if message.receiver_id == employer_id and not message.is_read:
            message.mark_as_read()

    return render_template(
        'employer/chat.html',
        messages=messages,
        user=user,
        job=job,
        job_id=job_id
    )


@employer_bp.route('/messages', methods=['GET'])
@auth_required(user_type='employer')
def view_all_chats():
    employer_id = g.user.employer_id

    # Get all unique conversations for this employer
    response = DynamoDB.scan(
        'Messages',
        FilterExpression='sender_id = :employer_id OR receiver_id = :employer_id',
        ExpressionAttributeValues={':employer_id': employer_id}
    )

    messages = response.get('Items', [])

    # Create a dictionary to store the latest message for each conversation
    # Use combination of user_id and job_id as key
    conversations = {}
    for msg in messages:
        message = Message(**msg)
        other_id = message.receiver_id if message.sender_id == employer_id else message.sender_id

        # Create a unique key combining user_id and job_id
        conversation_key = f"{other_id}_{message.job_id}"

        if (conversation_key not in conversations or
                message.timestamp > conversations[conversation_key]['latest_message'].timestamp):
            # Get the user information
            user = User.get_by_id(other_id)
            # Get the job information
            job = Job.get_by_id(message.job_id) if message.job_id else None

            if user:
                conversations[conversation_key] = {
                    'user': user,
                    'latest_message': message,
                    'unread_count': 0,
                    'job_id': message.job_id,
                    'job_title': job.job_title if job else 'General Discussion'
                }

    # Count unread messages for each conversation
    for conv_key in conversations:
        user_id = conv_key.split('_')[0]
        job_id = conversations[conv_key]['job_id']

        unread_count = DynamoDB.scan(
            'Messages',
            FilterExpression=('sender_id = :other_id AND receiver_id = :employer_id '
                              'AND is_read = :is_read AND job_id = :job_id'),
            ExpressionAttributeValues={
                ':other_id': user_id,
                ':employer_id': employer_id,
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

    return render_template('employer/messages.html', conversations=sorted_conversations)


@employer_bp.route('/messages/stream')
@auth_required(user_type='employer')
def stream_messages():
    from flask import copy_current_request_context, current_app

    employer_id = g.user.employer_id
    app = current_app._get_current_object()

    @copy_current_request_context
    def generate():
        last_check = dt.now(timezone.utc).isoformat()
        sent_message_ids = set()  # Track sent message IDs

        try:
            while True:
                with app.app_context():
                    try:
                        new_messages = Message.get_new_messages(employer_id, last_check, user_type='employer')

                        if new_messages:
                            for message in new_messages:
                                if message.message_id not in sent_message_ids:
                                    sent_message_ids.add(message.message_id)
                                    data = {
                                        'message_id': message.message_id,
                                        'content': message.content,
                                        'timestamp': message.timestamp,
                                        'sender_type': message.sender_type,
                                        'sender_id': message.sender_id,
                                        'receiver_id': message.receiver_id,
                                        'job_id': message.job_id,
                                        'conversation_id': f'{message.sender_id}_{message.job_id}',
                                        'is_read': message.is_read
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