"""أوامر CLI: init-db, seed-db."""
import click
from flask.cli import with_appcontext

from app.extensions import db
from app.models import Role, User
from app.models.role import ROLE_NAMES


DEMO_USERS = [
    # username, email, name, role, password (تطوير فقط)
    ("citizen_demo",    "citizen@example.test",     "مواطن تجريبي",        "citizen",            "citizen-dev-pass"),
    ("police_demo",     "police@example.test",      "ضابط تجريبي",         "police_officer",     "police-dev-pass"),
    ("operations_demo", "operations@example.test",  "مدير عمليات تجريبي",  "operations_manager", "ops-dev-pass"),
    ("director_demo",   "director@example.test",    "مدير عام تجريبي",     "director",           "director-dev-pass"),
    ("admin_demo",      "admin@example.test",       "مسؤول نظام تجريبي",   "administrator",      "admin-dev-pass"),
]


def register_cli(app):
    app.cli.add_command(init_db)
    app.cli.add_command(seed_db)


@click.command("init-db")
@with_appcontext
def init_db():
    """ينشئ قاعدة البيانات والجداول."""
    db.create_all()
    click.echo("✓ تم إنشاء الجداول.")


@click.command("seed-db")
@with_appcontext
def seed_db():
    """ينشئ الأدوار والمستخدمين التجريبيين (بدون تكرار)."""
    db.create_all()

    # الأدوار
    for name, label in ROLE_NAMES.items():
        existing = db.session.execute(
            db.select(Role).where(Role.name == name)
        ).scalar_one_or_none()
        if not existing:
            db.session.add(Role(name=name, label=label))
    db.session.commit()
    click.echo("✓ الأدوار جاهزة.")

    # المستخدمون
    created = 0
    for username, email, name, role_name, password in DEMO_USERS:
        exists = db.session.execute(
            db.select(User).where((User.username == username) | (User.email == email))
        ).scalar_one_or_none()
        if exists:
            continue
        role = db.session.execute(
            db.select(Role).where(Role.name == role_name)
        ).scalar_one()
        user = User(username=username, email=email, name=name, role=role, is_active=True)
        user.set_password(password)
        db.session.add(user)
        created += 1
    db.session.commit()
    click.echo(f"✓ تم إنشاء {created} مستخدمًا تجريبيًا (Development Only).")