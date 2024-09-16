# Sample controller

from flask import Blueprint
from app.models.job import Job
from app.views.job_views import render_job_list

jobs = Blueprint('jobs', __name__)

@jobs.route('/jobs')
def list_jobs():
    jobs = [
        Job("Software Engineer", "Develop web applications", "Tech Co", "Melbourne", "$100,000"),
        Job("Data Analyst", "Analyze business data", "Data Corp", "Sydney", "$80,000")
    ]
    return render_job_list(jobs)