# src/controllers/admin_controller.py

from ..models.admin_model import Admin
import bcrypt

class AdminController:
    @staticmethod
    def login(email, password):
        admin = Admin.get_by_email(email)
        if admin and bcrypt.checkpw(password.encode('utf-8'), admin.password.encode('utf-8')):
            return admin, None
        return None, "Invalid email or password."

    # Add admin-specific registration if needed
