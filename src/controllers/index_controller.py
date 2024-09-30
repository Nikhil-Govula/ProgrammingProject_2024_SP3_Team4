# src/controllers/index_controller.py

from ..models.user_model import User
from ..models.employer_model import Employer
from ..models.admin_model import Admin

def get_user(user_id, user_type):
    if user_type == 'user':
        return User.get_by_id(user_id)
    elif user_type == 'employer':
        return Employer.get_by_email(user_id)  # Assuming user_id is email for employers
    elif user_type == 'admin':
        return Admin.get_by_email(user_id)  # Assuming user_id is email for admins
    else:
        return None
