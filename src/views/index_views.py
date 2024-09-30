from flask import Blueprint, render_template, redirect, url_for, g

from ..controllers.index_controller import get_user
from ..decorators.auth_required import auth_required

index_bp = Blueprint('index_bp', __name__)

@index_bp.route('/Index')
@auth_required()  # Using the updated decorator without specifying user_type
def index():
    user = get_user(g.user.user_id, g.user_type)  # Fetch user based on user_type
    if user:
        user_info = user.to_dict()
        return render_template('index.html', user=user_info)
    else:
        return redirect(url_for('landing.landing'))

# @index_bp.route('/')
# def root():
#     if g.user:
#         return redirect(url_for('index_bp.index'))
#     else:
#         return redirect(url_for('landing.landing'))
