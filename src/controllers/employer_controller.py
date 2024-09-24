from ..models.employer_model import Employer
import bcrypt

class CompanyController:
    @staticmethod
    def login(email, password):
        employer = Employer.get_by_email(email)
        if employer and bcrypt.checkpw(password.encode('utf-8'), employer.password.encode('utf-8')):
            return employer
        return None