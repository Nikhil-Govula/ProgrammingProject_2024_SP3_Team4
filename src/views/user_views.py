from flask import Blueprint, render_template
from ..controllers.user_controller import get_user

users = Blueprint('users', __name__)

@users.route('/')
def index():
    user = get_user()
    return render_template('index.html', user=user)