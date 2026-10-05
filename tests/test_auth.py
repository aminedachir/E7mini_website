"""اختبارات المصادقة."""
from app.models import User
from app.extensions import db


def test_password_hashing(app, make_user):
    user = make_user("u1", "u1@test.local", "citizen", "s3cret-pass")
    assert user.password_hash != "s3cret-pass"
    assert user.check_password("s3cret-pass")
    assert not user.check_password("wrong")


def test_login_success(client, make_user):
    make_user("loginuser", "login@test.local", "citizen", "pass12345")
    r = client.post(
        "/login",
        data={"email": "login@test.local", "password": "pass12345"},
        follow_redirects=False,
    )
    assert r.status_code in (302, 303)


def test_login_wrong_password(client, make_user):
    make_user("wrongpw", "wrong@test.local", "citizen", "correct-pass")
    r = client.post(
        "/login",
        data={"email": "wrong@test.local", "password": "bad"},
    )
    assert r.status_code == 200


def test_login_inactive_user(client, make_user):
    make_user("inactive", "inactive@test.local", "citizen", "pass12345", active=False)
    r = client.post(
        "/login",
        data={"email": "inactive@test.local", "password": "pass12345"},
    )
    assert r.status_code == 200


def test_login_unknown_user(client):
    r = client.post(
        "/login",
        data={"email": "ghost@test.local", "password": "anything"},
    )
    assert r.status_code == 200


def test_logout(client, make_user):
    make_user("logoutuser", "logout@test.local", "citizen", "pass12345")
    client.post(
        "/login",
        data={"email": "logout@test.local", "password": "pass12345"},
    )
    r = client.post("/logout", follow_redirects=False)
    assert r.status_code in (302, 303)