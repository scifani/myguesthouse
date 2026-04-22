import logging
import os

from flask import Flask, jsonify, make_response, redirect, request, url_for
from flask_login import LoginManager

from web.translations import LANGUAGES, DEFAULT_LANG, TRANSLATIONS
from web.config_loader import resolve_text

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

    @app.route('/set-lang/<code>')
    def set_lang(code):
        if code not in LANGUAGES:
            code = DEFAULT_LANG
        dest = request.referrer or url_for('public.index')
        resp = make_response(redirect(dest))
        resp.set_cookie('lang', code, max_age=60 * 60 * 24 * 365, samesite='Lax')
        return resp

    @app.context_processor
    def inject_globals():
        lang = request.cookies.get('lang', DEFAULT_LANG)
        if lang not in LANGUAGES:
            lang = DEFAULT_LANG
        t = TRANSLATIONS[lang]

        def resolve(value):
            return resolve_text(value, lang)

        return {
            'site': site,
            'lang': lang,
            'languages': LANGUAGES,
            't': t,
            'resolve': resolve,
        }

    from web.blueprints.public import public_bp
    from web.blueprints.admin import admin_bp
    app.register_blueprint(public_bp)
    app.register_blueprint(admin_bp)

    return app


app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=os.environ.get('FLASK_DEBUG', '') == '1')
