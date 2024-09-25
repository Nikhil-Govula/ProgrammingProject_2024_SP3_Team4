from ..models.employer_model import Employer
import bcrypt

class EmployerController:
    @staticmethod
    def login(email, password):
        company = Employer.get_by_email(email)
        if company and bcrypt.checkpw(password.encode('utf-8'), company.password.encode('utf-8')):
            return company
        return None