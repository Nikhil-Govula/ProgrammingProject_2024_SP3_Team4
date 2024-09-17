from flask import Flask
from .views.job_views import jobs
from .views.index_views import indexs
from .views.login_views import logins

def create_app():
    application = app = Flask(__name__)
    application.register_blueprint(jobs)
    application.register_blueprint(indexs)
    application.register_blueprint(logins)
    return application