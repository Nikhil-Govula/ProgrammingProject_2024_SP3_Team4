# Sample controller

from flask import Blueprint, render_template
from ..models.job import Job

jobs = Blueprint('jobs', __name__)

@jobs.route('/jobs')
def list_jobs():
    jobs = [
        Job("Software Engineer", "Develop web applications", "Tech Co", "Melbourne", "$100,000"),
        Job("Data Analyst", "Analyze business data", "Data Corp", "Sydney", "$80,000")
    ]
    return render_template('jobs.html', jobs=jobs)