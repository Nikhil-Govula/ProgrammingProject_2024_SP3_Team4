from flask import Flask
from .controllers import users, jobs

def create_app():
    app = Flask(__name__)
    app.register_blueprint(users)
    app.register_blueprint(jobs)
    return app