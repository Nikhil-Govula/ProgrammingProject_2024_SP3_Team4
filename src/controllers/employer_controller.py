# src/controllers/employer_controller.py

from ..models.employer_model import Employer
import bcrypt

class EmployerController:
    @staticmethod
    def login(email, password):
        employer = Employer.get_by_email(email)
        if employer and bcrypt.checkpw(password.encode('utf-8'), employer.password.encode('utf-8')):
            return employer, None
        return None, "Invalid email or password."

    @staticmethod
    def register_employer(email, password, company_name, contact_person, phone_number):
        existing_employer = Employer.get_by_email(email)
        if existing_employer:
            return False, "An employer with this email already exists."

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        new_employer = Employer(
            company_name=company_name,
            email=email,
            password=hashed_password,
            contact_person=contact_person,
            phone_number=phone_number
        )
        new_employer.save()
        return True, "Employer registered successfully."
