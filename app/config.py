import os
import secrets

basedir = os.path.abspath(os.path.dirname(__file__))


def _fix_db_url(url: str) -> str:
    """Render/Heroku retournent 'postgres://' — SQLAlchemy 2.x exige 'postgresql://'."""
    if url and url.startswith('postgres://'):
        return url.replace('postgres://', 'postgresql://', 1)
    return url


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY') or secrets.token_hex(32)

    _db_url = os.getenv('DATABASE_URL') or f"sqlite:///{os.path.join(basedir, '..', 'instance', 'tbtrack.db')}"
    SQLALCHEMY_DATABASE_URI = _fix_db_url(_db_url)
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    WTF_CSRF_ENABLED = True

    # Sécurité session
    SESSION_COOKIE_SECURE = os.getenv('FLASK_ENV') == 'production'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
