from flask import Flask
from .views.job_views import jobs
from .views.index_views import indexs
from .views.login_views import logins
from .views.register_views import registers
import os
print("Template folder path:", os.path.abspath('src/templates'))

def create_app():
    # Specify the template folder explicitly
    template_dir = os.path.abspath('src/templates')
    application = Flask(__name__, template_folder=template_dir)

    application.config['TEMPLATES_AUTO_RELOAD'] = True  # Enable template auto-reload

    # Register blueprints
    application.register_blueprint(jobs)
    application.register_blueprint(indexs)
    application.register_blueprint(logins)
    application.register_blueprint(registers)

    return application
