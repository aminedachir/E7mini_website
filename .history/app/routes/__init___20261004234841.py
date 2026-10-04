"""تسجيل جميع الـ Blueprints في مكان واحد."""
from flask import Flask


def register_blueprints(app: Flask) -> None:
    from app.routes.auth import auth_bp
    from app.routes.complaints import complaints_bp
    from app.routes.main import main_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(complaints_bp)