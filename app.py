from flask import Flask, render_template, redirect, url_for
from config import Config
from models import db, User
from flask_login import LoginManager
from flask_migrate import Migrate
import os

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    migrate = Migrate(app, db)
    login = LoginManager(app)
    login.login_view = 'auth.login'

    @login.user_loader
    def load_user(id):
        return db.session.get(User, int(id))

    # Ensure directories exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['MANUALS_FOLDER'], exist_ok=True)

    # Register Blueprints (Placeholder for now)
    from routes.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from routes.dashboard import bp as dashboard_bp
    app.register_blueprint(dashboard_bp)

    from routes.edition import bp as edition_bp
    app.register_blueprint(edition_bp)

    from routes.manuals import bp as manuals_bp
    app.register_blueprint(manuals_bp)

    from routes.calendar import bp as calendar_bp
    app.register_blueprint(calendar_bp)

    from routes.users import bp as users_bp
    app.register_blueprint(users_bp)

    from routes.countries import bp as countries_bp
    app.register_blueprint(countries_bp)

    from routes.embassies import bp as embassies_bp
    app.register_blueprint(embassies_bp)

    from routes.articles import bp as articles_bp
    app.register_blueprint(articles_bp)

    @app.route('/')
    def index():
        return redirect(url_for('auth.login'))

    return app

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run(debug=True)
