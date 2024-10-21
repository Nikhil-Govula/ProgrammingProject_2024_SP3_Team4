# src/views/employer_views.py

from flask import Blueprint, render_template, request, redirect, url_for, make_response, g, flash, jsonify
from ..controllers import EmployerController
from ..decorators.auth_required import auth_required
from ..services import SessionManager
from ..models import Job

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

@employer_bp.route('/dashboard', methods=['GET'])
@auth_required(user_type='employer')
def dashboard():
    employer = g.user
    return render_template('employer/dashboard.html', employer=employer)

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

@employer_bp.route('/jobs', methods=['GET'])
@auth_required(user_type='employer')
def view_jobs():
    employer_id = g.user.employer_id
    all_jobs = EmployerController.list_employer_jobs(employer_id)
    return render_template('employer/view_jobs.html', jobs=all_jobs)

@employer_bp.route('/jobs/create', methods=['GET', 'POST'])
@auth_required(user_type='employer')
def create_job():
    if request.method == 'POST':
        job_title = request.form['job_title']
        description = request.form['description']
        requirements = request.form['requirements']
        salary = request.form['salary']
        location = request.form['city']  # Combined city and country field
        certifications = request.form.getlist('certifications[]')  # Changed to 'certifications[]'
        skills = request.form.getlist('skills[]')  # Changed to 'skills[]'
        work_history = request.form['work_history']
        company_name = g.user.company_name  # Assuming employer's company name

        # Split location into city and country
        try:
            city, country = map(str.strip, location.split(',', 1))
            print(f"City: {city}, Country: {country}")  # Log parsed values
        except ValueError:
            flash("Invalid location format. Please use 'City, Country'.", 'error')
            return render_template('employer/create_job.html')

        success, message = EmployerController.create_job(
            employer_id=g.user.employer_id,
            job_title=job_title,
            description=description,
            requirements=requirements,
            salary=salary,
            city=city,  # Pass the parsed city
            country=country,  # Pass the parsed country
            certifications=certifications,
            skills=skills,
            work_history=work_history,
            company_name=company_name
        )

        if success:
            flash(message, 'success')
            return redirect(url_for('employer_views.view_jobs'))
        else:
            flash(message, 'error')
            return render_template('employer/create_job.html')

    return render_template('employer/create_job.html')

@employer_bp.route('/jobs/edit/<job_id>', methods=['GET', 'POST'])
@auth_required(user_type='employer')
def edit_job(job_id):
    job = Job.get_by_id(job_id)
    if not job or job.employer_id != g.user.employer_id:
        flash("Job not found or you don't have permission to edit this job.", 'error')
        return redirect(url_for('employer_views.view_jobs'))

    if request.method == 'POST':
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
            return redirect(url_for('employer_views.view_jobs'))
        else:
            flash(message, 'error')

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

@employer_bp.route('/jobs/delete/<job_id>', methods=['POST'])
@auth_required(user_type='employer')
def delete_job(job_id):
    success, message = EmployerController.delete_job(job_id)
    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')
    return redirect(url_for('employer_views.view_jobs'))
