# Sample controller

from flask import Blueprint, render_template
from app.models.user import User

users = Blueprint('users', __name__)

@users.route('/')
def index():
    user = User('test_user', 'test@example.com')
    return render_template('index.html', user=user)