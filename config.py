from dotenv import load_dotenv
import os

load_dotenv()  # Load environment variables from .env

class Config:
    SECRET_KEY = 'secret_key'
    DEBUG = True