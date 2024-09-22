# ProgrammingProject_2024_SP3_Team4
NAZ team Programming Project1 3Q2024

# SDK
Python 3.11 - latest version natively supported on aws

# How to run local instance:
Open the root directory and run below commands in the terminal.
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python run.py

# How to run on Mac Book

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python application.py
deactivate <- Once finished

Local instance should now be running on http://127.0.0.1:5000/
Change port number if not working as it is likely already reserved on your machine.

# Cloud instance
NOTE: run.py to be named application.py, flask instance in application.py to be initialised as application = app = create_app() and subsequently called with application (not app). 'App' folder to be renamed as anything but 'App' or 'Application' (src or project name seems to be the convention). __init__.py create_app() method to initialise flask as application = app = Flask(__name__) (same as application.py)

When zipping content, do not zip the folder, rather highlight all the contents in the folder and zip this way (this allows for the files, especially application.py to be in the root of the zip rather than a folder being in the root)

AWS documentation tutorial for creating beanstalk application: https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/GettingStarted.CreateApp.html

# Deploy app via CLI setup
1. Check if AWS CLI already installed
> aws --version
2. Install latest AWS CLI for your operating system if not installed
https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html
3. Check if Elastic Beanstalk CLI already installed
> eb --version
4. Install latest Elastic Beanstalk CLI if not installed
> pip install awsebcli
5. Configure AWS CLI
i. Setup access key in AWS console.
Sign in to AWS account in browser and click username drop down menu on top right corner then open Security credentials.
Scroll down to Access keys and click Create access key. Ignore root user warning for now and click Create access key(We may change this later).
Leave this page open as we will need those keys, can create a new access key any time if original is lost.
ii. Configure AWS CLI with access keys
> aws configure
AWS Access Key ID = Access key
AWS Secret Access Key = Secret access key
Default region (us-east-1) = Press enter for default
Default output format [None]: Not required, Press enter
6. Configure EB CLI
> eb init 
Select a default region =  1 for us-east-1
Select an application to use = Select previously created elastic beanstalk app
Do you wish to continue with CodeCommit? (Y/n): n as we are using github for vc
Elastic Beanstalk CLI now fully configured and .elasticbeanstalk directory should appear with config.yml file inside
7. Deploy project (Once configured, this will be the only prompt you need to enter)
> eb deploy




# Project structure
Models = models
Views = templates
Controller Views = views
Controllers = controllers
AWS services = services
config.py = AWS services to be organised here, however, keys are to be stored in .env file.
.env = Any AWS keys will be stored here, however file wil not be included in git repo for security purposes.
