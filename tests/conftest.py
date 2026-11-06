import os
from pathlib import Path
import secrets
import pymysql
import pytest

@pytest.fixture(scope='session')
def app():
    root=Path(__file__).resolve().parents[1]
    password=(root/'.local/mysql-root.txt').read_text(encoding='utf-8')
    connection=pymysql.connect(host='127.0.0.1',port=3307,user='root',password=password,autocommit=True)
    name='chaplin_test_'+secrets.token_hex(6)
    with connection.cursor() as cursor:
        cursor.execute(f'CREATE DATABASE `{name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci')
    os.environ['DATABASE_URL']=f'mysql+pymysql://root:{password}@127.0.0.1:3307/{name}'
    from config import Config
    Config.SQLALCHEMY_DATABASE_URI=os.environ['DATABASE_URL']
    from app import app as application
    application.config.update(TESTING=True,PAYMENT_DEMO_MODE=True)
    from extensions import db
    from schema import initialize
    from seed_demo import seed
    from models import User
    from werkzeug.security import generate_password_hash
    with application.app_context():
        initialize();seed(write_credentials=False)
        for account in User.query.all():
            account.password=generate_password_hash('TestPassword123!')
        db.session.add(User(login='outsider',email='outsider@example.local',first_name='Інший',last_name='Гість',password=generate_password_hash('TestPassword123!'),bought_tickets_summary=0,role='customer'))
        db.session.commit()
    yield application
    with application.app_context():
        db.session.remove();db.engine.dispose()
    assert name.startswith('chaplin_test_') and len(name)==25
    with connection.cursor() as cursor:
        cursor.execute(f'DROP DATABASE `{name}`')
    connection.close()
