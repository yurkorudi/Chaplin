"""Local configuration. Environment variables take precedence over .env."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
for line in (ROOT / '.env').read_text(encoding='utf-8').splitlines() if (ROOT / '.env').exists() else []:
    if line.strip() and not line.lstrip().startswith('#') and '=' in line:
        key, value = line.split('=', 1)
        os.environ.setdefault(key.strip(), value.strip().strip('\"').strip("'"))

class Config:
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'mysql+pymysql://chaplin@127.0.0.1:3307/chaplin_demo')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {'pool_pre_ping': True, 'pool_recycle': 280}
    SECRET_KEY = os.environ.get('SECRET_KEY')
    PAYMENT_DEMO_MODE = os.environ.get('PAYMENT_DEMO_MODE', 'false').lower() == 'true'
    TEMPLATES_AUTO_RELOAD = PAYMENT_DEMO_MODE
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'false').lower() == 'true'
    MAX_CONTENT_LENGTH = 4 * 1024 * 1024
    UPLOAD_FOLDER = str(ROOT / 'uploads')
    HOLD_MINUTES = 10
    SESSION_BUFFER_MINUTES = 15
    LIQPAY_PUBLIC_KEY = os.environ.get('LIQPAY_PUBLIC_KEY','')
    LIQPAY_PRIVATE_KEY = os.environ.get('LIQPAY_PRIVATE_KEY','')
    PUBLIC_BASE_URL = os.environ.get('PUBLIC_BASE_URL','').rstrip('/')
