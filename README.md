# ProgrammingProject_2024_SP3_Team4
NAZ team Programming Project1 3Q2024

# SDK
Python 3.12

# How to run local instance:
Open the root directory and run below commands in the terminal.
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python run.py

Local instance should now be running on http://127.0.0.1:5000/
Change port number if not working as it is likely already reserved on your machine.

# Cloud instance
To be implemented via elastic beanstalk (Not yet setup).

# Project structure
Models = models
Views = templates
Controller Views = views
Controllers = controllers
AWS services = services
config.py = AWS services to be organised here, however, keys are to be stored in .env file.
.env = Any AWS keys will be stored here, however file wil not be included in git repo for security purposes.