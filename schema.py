"""Additive schema upgrade. Back up existing databases before applying changes."""
from extensions import db
from sqlalchemy import inspect, text
from pathlib import Path
from datetime import datetime
import os
import subprocess

def backup_database():
    url=db.engine.url
    folder=Path('.local/backups');folder.mkdir(parents=True,exist_ok=True)
    executable=Path(os.environ.get('MYSQLD_PATH',r'C:\Program Files\MySQL\MySQL Server 8.0\bin\mysqld.exe')).with_name('mysqldump.exe')
    if not executable.exists():
        raise RuntimeError('mysqldump is required to back up the existing database before migration.')
    target=folder/f'{url.database}-{datetime.now():%Y%m%d-%H%M%S}.sql'
    environment=os.environ.copy();environment['MYSQL_PWD']=url.password or ''
    subprocess.run([str(executable),f'--host={url.host}',f'--port={url.port or 3306}',f'--user={url.username}','--single-transaction','--no-tablespaces','--default-character-set=utf8mb4',f'--result-file={target}',url.database],check=True,env=environment,capture_output=True)
    return target

def initialize():
    inspector = inspect(db.engine)
    existing = set(inspector.get_table_names())
    if existing and not db.engine.url.database.startswith('chaplin_test_'):
        backup_database()
    additions = {
        'sessions': {'price': 'NUMERIC(10,2) NOT NULL DEFAULT 150', 'vip_multiplier': 'NUMERIC(4,2) NOT NULL DEFAULT 1.5'},
        'users': {'phone': 'VARCHAR(25)', 'role': "VARCHAR(20) NOT NULL DEFAULT 'customer'"},
        'seats': {'column_index': 'INTEGER NULL'},
        'tickets': {'order_id': 'VARCHAR(36) NULL', 'token': 'VARCHAR(64) NULL'},
        'orders': {'fulfillment_status': "VARCHAR(20) NOT NULL DEFAULT 'pending'"},
    }
    # create_all creates only missing tables; no tables are dropped.
    db.create_all()
    for table, columns in additions.items():
        if table not in existing:
            continue
        present = {c['name'] for c in inspect(db.engine).get_columns(table)}
        for name, definition in columns.items():
            if name not in present:
                db.session.execute(text(f'ALTER TABLE `{table}` ADD COLUMN `{name}` {definition}'))
    db.session.commit()
    if 'tickets' in existing:
        duplicates = db.session.execute(text('SELECT session_id, row_index, column_index FROM tickets GROUP BY session_id, row_index, column_index HAVING COUNT(*) > 1 LIMIT 1')).first()
        if duplicates:
            raise RuntimeError('Existing duplicate tickets require review; no data was removed.')
        db.session.execute(text('ALTER TABLE tickets MODIFY cost NUMERIC(10,2) NOT NULL'))
        indexes = inspect(db.engine).get_indexes('tickets')
        for name, columns in [('uq_ticket_position', 'session_id,row_index,column_index'), ('uq_ticket_token', 'token')]:
            if not any(i.get('unique') and i['column_names']==columns.split(',') for i in indexes):
                db.session.execute(text(f'CREATE UNIQUE INDEX {name} ON tickets ({columns})'))
        if not any(fk['constrained_columns']==['order_id'] for fk in inspect(db.engine).get_foreign_keys('tickets')):
            db.session.execute(text('ALTER TABLE tickets ADD CONSTRAINT fk_ticket_order FOREIGN KEY (order_id) REFERENCES orders(id)'))
        indexes=inspect(db.engine).get_indexes('seats')
        if not any(i.get('unique') and i['column_names']==['session_id','row','column_index'] for i in indexes):
            db.session.execute(text('CREATE UNIQUE INDEX uq_seat_position ON seats(session_id, `row`, column_index)'))
        db.session.commit()
