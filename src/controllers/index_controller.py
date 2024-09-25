# src/controllers/index_controller.py

from ..models.user_model import User

def get_user_by_id(user_email):
    return User.get_by_email(user_email)
