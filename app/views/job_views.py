from flask import render_template

def render_job_list(jobs):
    return render_template('jobs.html', jobs=jobs)