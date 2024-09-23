from flask import Blueprint, request, jsonify, render_template
from models import UserModel, JobModel, ApplicationModel
import uuid

users = Blueprint('users', __name__)

user_model = UserModel()
job_model = JobModel()
application_model = ApplicationModel()

# Endpoint to view available jobs
@users.route('/user/jobs', methods=['GET'])
def view_jobs():
    jobs = job_model.get_all_jobs()  # Assumes a method to get all jobs
    return jsonify({'jobs': jobs})

# Endpoint to apply for a job
@users.route('/user/apply_job', methods=['POST'])
def apply_job():
    data = request.json
    # Generate a unique application ID
    application_id = str(uuid.uuid4())
    application_data = {
        'application_id': application_id,
        'job_id': data['job_id'],
        'user_id': data['user_id'],  # Assumes user_id is passed
        'cover_letter': data['cover_letter'],
        'application_status': 'Pending',
        'applied_at': data['applied_at']
    }
    application_model.create_application(application_data)
    return jsonify({'message': 'Application submitted successfully!', 'application_id': application_id}), 201

# Endpoint to view user's applications and their status
@users.route('/user/applications/<user_id>', methods=['GET'])
def view_user_applications(user_id):
    applications = application_model.get_applications_by_user(user_id)
    return jsonify({'applications': applications})

# Endpoint to render the user dashboard
@users.route('/user/dashboard/<user_id>', methods=['GET'])
def user_dashboard(user_id):
    return render_template('user/user_dashboard.html', user_id=user_id)
