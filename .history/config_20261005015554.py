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


def _is_postgres(url: str) -> bool:
    return url.startswith("postgresql://") or url.startswith("postgres://")


class Config:
    APP_NAME = os.environ.get("APP_NAME", "احميني")
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-me")

    SQLALCHEMY_DATABASE_URI = _database_url(
        "sqlite:///" + os.path.join(BASE_DIR, "instance", "app.db")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # خيارات محرك SQLAlchemy — مهمة لـ Neon (PostgreSQL سحابي)
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,   # يفحص الاتصال قبل الاستخدام
        "pool_recycle": 240,     # يعيد تدوير الاتصال كل 4 دقائق (Neon يقطع بعد 5)
    }

    JSON_AS_ASCII = False
    WTF_CSRF_ENABLED = True

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    # تخزين مرفقات الشكاوى (خارج static لعدم كشفها بروابط عامة)
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "app", "uploads")
    MAX_CONTENT_LENGTH = 25 * 1024 * 1024
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
    SQLALCHEMY_ENGINE_OPTIONS = {}  # لا حاجة لإعدادات Neon في الاختبارات
    RATELIMIT_ENABLED = False


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True

    @classmethod
    def validate(cls):
        if cls.SECRET_KEY == "dev-only-change-me":
            raise RuntimeError("يجب تعيين SECRET_KEY آمن في بيئة الإنتاج.")
        if not _is_postgres(cls.SQLALCHEMY_DATABASE_URI):
            raise RuntimeError("بيئة الإنتاج تتطلب قاعدة بيانات PostgreSQL.")


config = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}