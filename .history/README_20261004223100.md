# نظام إدارة العمليات والشكاوى — Police Platform

منصة Flask بنظامين في مشروع واحد:

1. بوابة المواطن لتقديم البلاغات والشكاوى.
2. لوحة عمليات داخلية للشرطة لاستقبال وإدارة البلاغات والحوادث.

> **المرحلة الحالية: 2 — الهوية البصرية والواجهة المتجاوبة.**
> المنجز: الأساس المعماري، الهوية البصرية RTL، تسجيل الدخول/التسجيل/الخروج الأساسي.
> غير منجز بعد: الشكاوى، لوحة العمليات، API، الأدوار والصلاحيات.

## التقنيات

Python 3 · Flask (Application Factory + Blueprints) · Jinja2 · Flask-SQLAlchemy ·
Flask-Migrate · Flask-Login · Flask-WTF · python-dotenv · SQLite (تطوير) · PostgreSQL (لاحقًا)

## التشغيل

```bash
python -m venv venv
source venv/bin/activate        # على Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # ثم عدّل SECRET_KEY
python run.py
```

افتح: <http://127.0.0.1:5000>

## قاعدة البيانات والهجرات

بعد التثبيت (وبعد كل تحديث يضيف هجرات) نفّذ:

```bash
flask --app run db upgrade      # ينشئ جدول users
```

عند تغيير النماذج:

```bash
flask --app run db migrate -m "وصف التغيير"
flask --app run db upgrade
```

## شعار الشرطة

ضع ملف الشعار الرسمي كما هو (دون تعديل) في:

```
app/static/images/police-logo.png
```

يظهر تلقائيًا في الشريط العلوي والصفحة الرئيسية وصفحتي الدخول والتسجيل دون إعادة تشغيل.
إلى أن يُوضع الملف تعمل الواجهة بدون صورة.

## الهوية البصرية

كل الألوان معرّفة كمتغيرات CSS في أعلى `app/static/css/main.css`
(أزرق `#1554B8`، كحلي `#0B2D5C`، أزرق فاتح `#EAF2FF`). الأحمر والبرتقالي والأخضر للحالات والتنبيهات فقط.
الخطوط: خطوط النظام العربية. لإضافة خط محلي ضعه في `app/static/fonts/` وفعّل كتلة `@font-face` الموجودة (معلّقة) في ملف CSS.
لا تُستخدم أي موارد خارجية (CDN) ولا تتبّع.

## الانتقال إلى PostgreSQL

ثبّت `psycopg2-binary` ثم عيّن في `.env`:

```
DATABASE_URL=postgresql://user:password@localhost:5432/police_platform
```

## هيكل المشروع

```
police_platform/
├── run.py                 # نقطة التشغيل
├── config.py              # إعدادات (Development / Testing / Production)
├── requirements.txt
├── .env.example
├── app/
│   ├── __init__.py        # create_app() — Application Factory
│   ├── extensions.py      # db, migrate, login_manager, csrf
│   ├── models/            # نماذج قاعدة البيانات
│   ├── routes/            # Blueprints: main, auth
│   ├── forms/             # نماذج Flask-WTF
│   ├── services/          # منطق الأعمال
│   ├── templates/         # base, home, auth/, components/ (RTL عربي)
│   └── static/            # css, js, images, vendor, fonts
└── migrations/            # Alembic (Flask-Migrate)
```
