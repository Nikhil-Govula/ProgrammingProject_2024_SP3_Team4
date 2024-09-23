from flask import Blueprint, request, jsonify, render_template
from ..models.employers import EmployerModel
from ..models.jobs import JobModel
from ..models.applications import ApplicationModel
import uuid

employers = Blueprint('employers', __name__)

employer_model = EmployerModel()
job_model = JobModel()
application_model = ApplicationModel()

# Endpoint to create a job
@employers.route('/employer/create_job', methods=['POST'])
def create_job():
    data = request.json
    # Generate a unique job ID
    job_id = str(uuid.uuid4())
    job_data = {
        'job_id': job_id,
        'employer_id': data['employer_id'],  # Assumes employer_id is passed
        'job_title': data['job_title'],
        'job_description': data['job_description'],
        'location': data['location'],
        'salary': data['salary'],
        'created_at': data['created_at']
    }
    job_model.create_job(job_data)
    return jsonify({'message': 'Job created successfully!', 'job_id': job_id}), 201

# Endpoint to list jobs posted by the employer
@employers.route('/employer/jobs/<employer_id>', methods=['GET'])
def list_jobs(employer_id):
    jobs = job_model.get_jobs_by_employer(employer_id)
    return jsonify({'jobs': jobs})

# Endpoint to view applications for a specific job
@employers.route('/employer/job_applications/<job_id>', methods=['GET'])
def view_applications(job_id):
    applications = application_model.get_applications_by_job(job_id)
    return jsonify({'applications': applications})

# Endpoint to update the status of an application
@employers.route('/employer/update_application_status', methods=['POST'])
def update_application_status():
    data = request.json
    application_model.update_application_status(data['application_id'], data['application_status'])
    return jsonify({'message': 'Application status updated successfully!'})

# Endpoint to render the employer dashboard
@employers.route('/employer/dashboard/<employer_id>', methods=['GET'])
def employer_dashboard(employer_id):
    return render_template('employer/employer_dashboard.html', employer_id=employer_id)
