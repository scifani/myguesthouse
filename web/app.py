import logging
import os

from flask import Flask, jsonify, redirect, request, url_for
from flask_login import LoginManager

logging.basicConfig(level=logging.INFO)


def create_app() -> Flask:
    app = Flask(__name__)
    app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-change-me')

    from web.config_loader import load_config
    try:
        site = load_config()
    except FileNotFoundError:
        site = {}

    login_manager = LoginManager()
    login_manager.init_app(app)

    from web.blueprints.admin import AdminUser

    @login_manager.user_loader
    def load_user(user_id):
        if user_id == 'admin':
            return AdminUser()
        return None

    @login_manager.unauthorized_handler
    def unauthorized():
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Non autenticato'}), 401
        return redirect(url_for('admin.login_page'))

    @app.context_processor
    def inject_site():
        return {'site': site}

    from web.blueprints.public import public_bp
    from web.blueprints.admin import admin_bp
    app.register_blueprint(public_bp)
    app.register_blueprint(admin_bp)

    return app


app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=os.environ.get('FLASK_DEBUG', '') == '1')
