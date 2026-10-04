"""Flask Application Factory."""
import os
from datetime import datetime

from flask import Flask

from config import config
from app.extensions import csrf, db, login_manager, migrate

LOGO_RELATIVE_PATH = os.path.join("images", "police-logo.png")


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

    return app


def _init_extensions(app: Flask) -> None:
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    login_manager.login_view = "auth.login"
    login_manager.login_message = "يرجى تسجيل الدخول للوصول إلى هذه الصفحة."
    login_manager.login_message_category = "warning"
    login_manager.session_protection = "strong"

    # استيراد النماذج ليتعرف عليها Flask-Migrate
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
        # يُفحص وجود الشعار عند كل طلب، فيظهر فور وضع الملف دون إعادة تشغيل.
        logo_file = os.path.join(app.static_folder, LOGO_RELATIVE_PATH)
        return {
            "APP_NAME": app.config["APP_NAME"],
            "CURRENT_YEAR": datetime.now().year,
            "LOGO_AVAILABLE": os.path.isfile(logo_file),
        }
