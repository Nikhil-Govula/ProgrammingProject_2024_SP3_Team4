from flask import Blueprint, render_template
# from ..controllers.job_controller import get_jobs

jobs = Blueprint('jobs', __name__)

@jobs.route('/jobs')
def list_jobs():
    # jobs = get_jobs()
    return render_template('jobs.html', jobs=jobs)