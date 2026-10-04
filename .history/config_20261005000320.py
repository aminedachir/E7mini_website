"""إعدادات التطبيق حسب البيئة."""
import os

from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))


def _database_url(default: str) -> str:
    """يقرأ DATABASE_URL ويصحح البادئة القديمة postgres:// إلى postgresql://."""
    url = os.environ.get("DATABASE_URL", default)
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


class Config:
    APP_NAME = os.environ.get("APP_NAME", "احميني")
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-me")

    SQLALCHEMY_DATABASE_URI = _database_url(
        "sqlite:///" + os.path.join(BASE_DIR, "police_platform.db")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JSON_AS_ASCII = False
    WTF_CSRF_ENABLED = True

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    # تخزين مرفقات البلاغات (خارج static لعدم كشفها بروابط عامة)
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "app", "uploads")
    MAX_CONTENT_LENGTH = 25 * 1024 * 1024  # 25 ميغابايت لكل طلب
    ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp", "gif"}
    ALLOWED_VIDEO_EXTENSIONS = {"mp4", "webm", "mov", "m4v"}

    # Flask-Limiter
    RATELIMIT_STORAGE_URI = "memory://"
    RATELIMIT_HEADERS_ENABLED = True


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    RATELIMIT_ENABLED = False


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True

    @classmethod
    def validate(cls):
        if cls.SECRET_KEY == "dev-only-change-me":
            raise RuntimeError("يجب تعيين SECRET_KEY آمن في بيئة الإنتاج.")


config = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}