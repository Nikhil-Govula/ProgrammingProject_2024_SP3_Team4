from flask import Flask
from .views.index_views import indexs
from .views.login_views import logins
from .views.register_views import registers
import os

def create_app():
    template_dir = os.path.abspath('src/templates')
    application = Flask(__name__, template_folder=template_dir)

    application.config['TEMPLATES_AUTO_RELOAD'] = True

    # Register blueprints
    application.register_blueprint(indexs)
    application.register_blueprint(logins)
    application.register_blueprint(registers)

    return application