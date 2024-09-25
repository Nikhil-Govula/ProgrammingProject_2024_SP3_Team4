from flask import Blueprint, render_template, redirect
from ..controllers.index_controller import get_user

index_bp = Blueprint('index', __name__)

@index_bp.route('/Index')
def index():
    user = get_user()
    # Pass only specific user details to the template
    user_info = {
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name
    }
    return render_template('index.html', user=user_info)

@index_bp.route('/')
def redirect_index():
    return redirect("/Index", code=302)