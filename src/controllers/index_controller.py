from ..models.user import User

def get_user():
    return User('test_user', 'test@example.com')