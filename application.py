import os

from src import create_app
from datetime import datetime

application = app = create_app()

if __name__ == '__main__':
    if os.getenv('FLASK_ENV') == 'production':
        application.run(host='0.0.0.0', port=443, ssl_context=('/etc/pki/tls/certs/server.crt', '/etc/pki/tls/certs/server.key'))
    else:
        application.run(host='0.0.0.0', port=8080)  # Default to non-SSL for development


        @app.template_filter('format_date')
        def format_date(value):
            """Format a date value to dd/mm/yyyy."""
            try:
                date_obj = datetime.strptime(value[:10], '%Y-%m-%d')
                return date_obj.strftime('%d/%m/%Y')
            except ValueError:
                return value  # If there is an error, return the original value


        # Register the filter
        app.jinja_env.filters['format_date'] = format_date