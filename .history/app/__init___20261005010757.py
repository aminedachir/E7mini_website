"""Flask Application Factory."""
import os
from datetime import datetime

from flask import Flask

from config import config
from app.extensions import csrf, db, limiter, login_manager, migrate

LOGO_BASENAME = "police-logo"
LOGO_EXTENSIONS = ("png", "jpg", "jpeg", "webp", "svg")
LOGO_DIR = "images"


def _find_logo_filename(static_folder: str) -> str | None:
    for ext in LOGO_EXTENSIONS:
        candidate = f"{LOGO_BASENAME}.{ext}"
        if os.path.isfile(os.path.join(static_folder, LOGO_DIR, candidate)):
            return candidate
    return None


def create_app(config_name: str | None = None) -> Flask:
    config_name = config_name or os.environ.get("FLASK_ENV", "development")
    config_class = config.get(config_name, config["default"])
    if hasattr(config_class, "validate"):
        config_class.validate()

    app = Flask(__name__)
    app.config.from_object(config_class)

    _init_extensions(app)
    _register_blueprints(app)
    _register_context_processors(app)
    _register_cli(app)

    return app


def _init_extensions(app: Flask) -> None:
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)

    upload_folder = app.config.get("UPLOAD_FOLDER")
    if upload_folder:
        os.makedirs(upload_folder, exist_ok=True)

    login_manager.login_view = "auth.login"
    login_manager.login_message = "يرجى تسجيل الدخول للوصول إلى هذه الصفحة."
    login_manager.login_message_category = "warning"
    login_manager.session_protection = "strong"

    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        try:
            return db.session.get(User, int(user_id))
        except (TypeError, ValueError):
            return None


def _register_blueprints(app: Flask) -> None:
    from app.routes import register_blueprints
    register_blueprints(app)


def _register_context_processors(app: Flask) -> None:
    @app.context_processor
    def inject_globals():
        logo_filename = _find_logo_filename(app.static_folder)
        return {
            "APP_NAME": app.config["APP_NAME"],
            "CURRENT_YEAR": datetime.now().year,
            "LOGO_AVAILABLE": logo_filename is not None,
            "LOGO_FILENAME": f"{LOGO_DIR}/{logo_filename}" if logo_filename else None,
        }


def _register_cli(app: Flask) -> None:
    from app.cli import register_cli
    register_cli(app)