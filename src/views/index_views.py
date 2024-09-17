from flask import Blueprint, render_template, redirect
from ..controllers.index_controller import get_user

indexs = Blueprint('index', __name__)

@indexs.route('/Index')
def index():
        user = get_user()
        return render_template('index.html', user=user)


@indexs.route('/')
def redirect_index():
    return redirect("/Index", code=302)
