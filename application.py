from src import create_app

application = app = create_app()

if __name__ == '__main__':
    application.run(host='0.0.0.0', port=443, ssl_context=('/etc/pki/tls/certs/server.crt', '/etc/pki/tls/certs/server.key'))
