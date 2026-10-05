"""اختبارات الأدوار والصلاحيات."""


def test_user_has_role(app, make_user):
    u = make_user("rolecheck", "rc@test.local", "police_officer", "pass12345")
    assert u.has_role("police_officer")
    assert not u.has_role("administrator")


def test_role_name_property(app, make_user):
    u = make_user("roleprop", "rp@test.local", "administrator", "pass12345")
    assert u.role_name == "administrator"


def test_all_roles_created(app):
    from app.models import Role
    from app.extensions import db
    names = {
        r.name for r in db.session.execute(db.select(Role)).scalars().all()
    }
    assert {
        "citizen", "police_officer", "operations_manager",
        "director", "administrator",
    }.issubset(names)