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
NOTE: run.py to be named application.py, flask instance in application.py to be initialised as application = app = create_app() and subsequently called with application (not app). 'App' folder to be renamed as anything but 'App' or 'Application' (src or project name seems to be the convention). __init__.py create_app() method to initialise flask as application = app = Flask(__name__) (same as application.py)

When zipping content, do not zip the folder, rather highlight all the contents in the folder and zip this way (this allows for the files, especially application.py to be in the root of the zip rather than a folder being in the root)

AWS documentation tutorial for creating beanstalk application: https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/GettingStarted.CreateApp.html  


# Project structure
Models = models
Views = templates
Controller Views = views
Controllers = controllers
AWS services = services
config.py = AWS services to be organised here, however, keys are to be stored in .env file.
.env = Any AWS keys will be stored here, however file wil not be included in git repo for security purposes.