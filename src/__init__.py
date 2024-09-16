from flask import Flask
from .controllers import users, jobs

def create_app():
    application = app = Flask(__name__)
    application.register_blueprint(users)
    application.register_blueprint(jobs)
    return application