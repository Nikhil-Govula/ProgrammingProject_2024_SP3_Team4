from flask import Flask
from .views.user_views import users
from .views.job_views import jobs

def create_app():
    application = app = Flask(__name__)
    application.register_blueprint(users)
    application.register_blueprint(jobs)
    return application