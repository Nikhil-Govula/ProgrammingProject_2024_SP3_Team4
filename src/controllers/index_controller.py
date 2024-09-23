from ..models.user_model import User

def get_user():
    # This is just a placeholder. In a real application, you'd fetch the user from the database or session.
    return User(
        username='test_user',
        email='test@example.com',
        password='placeholder_password',  # In reality, you'd never store plain text passwords
        first_name='Test',
        last_name='User',
        phone_number='1234567890'
    )