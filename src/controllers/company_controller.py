from ..models.company_model import Company
import bcrypt

class CompanyController:
    @staticmethod
    def login(email, password):
        company = Company.get_by_email(email)
        if company and bcrypt.checkpw(password.encode('utf-8'), company.password.encode('utf-8')):
            return company
        return None