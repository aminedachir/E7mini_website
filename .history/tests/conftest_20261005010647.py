"""إعداد pytest لاختبارات المشروع."""
import pytest

from app import create_app
from app.extensions import db
from app.models import Role, User
from app.models.role import ROLE_NAMES


@pytest.fixture
def app():
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        for name, label in ROLE_NAMES.items():
            db.session.add(Role(name=name, label=label))
        db.session.commit()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def make_user(app):
    def _make(username, email, role_name, password, active=True):
        role = db.session.execute(
            db.select(Role).where(Role.name == role_name)
        ).scalar_one()
        user = User(
            username=username, email=email, name=username,
            role=role, is_active=active,
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user
    return _make