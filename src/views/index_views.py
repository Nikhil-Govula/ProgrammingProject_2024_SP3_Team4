from flask import Blueprint, render_template, redirect
from ..controllers.index_controller import get_user

indexs = Blueprint('index', __name__)

@indexs.route('/Index')
def index():
    user = get_user()
    # You might want to pass only specific user details to the template
    return render_template('index.html', user={
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name
    })

@indexs.route('/')
def redirect_index():
    return redirect("/Index", code=302)