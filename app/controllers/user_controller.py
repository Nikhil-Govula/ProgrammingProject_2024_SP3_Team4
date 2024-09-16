# Sample controller

from flask import Blueprint
from app.models.user import User
from app.views.user_views import render_index

users = Blueprint('users', __name__)

@users.route('/')
def index():
    user = User('test_user', 'test@example.com')
    return render_index(user)