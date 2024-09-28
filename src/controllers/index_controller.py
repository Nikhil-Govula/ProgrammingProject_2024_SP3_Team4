# src/controllers/index_controller.py

from ..models.user_model import User

def get_user_by_id(user_id):
    return User.get_by_id(user_id)