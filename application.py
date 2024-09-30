import os

from src import create_app

application = app = create_app()

if __name__ == '__main__':
    if os.getenv('FLASK_ENV') == 'production':
        application.run(host='0.0.0.0', port=443, ssl_context=('/etc/pki/tls/certs/server.crt', '/etc/pki/tls/certs/server.key'))
    else:
        application.run(host='0.0.0.0', port=8080)  # Default to non-SSL for development