"""Start an isolated installed MySQL instance; never touch system services."""
from pathlib import Path
import os
import secrets
import socket
import subprocess
import time
import pymysql

ROOT = Path(__file__).resolve().parent
LOCAL = ROOT / '.local'

def port_open(port):
    with socket.socket() as sock:
        return sock.connect_ex(('127.0.0.1', port)) == 0

def main():
    LOCAL.mkdir(exist_ok=True)
    env = ROOT / '.env'
    if not env.exists():
        password = secrets.token_hex(20)
        env.write_text(f'DATABASE_URL=mysql+pymysql://chaplin:{password}@127.0.0.1:3307/chaplin_demo\nSECRET_KEY={secrets.token_hex(32)}\nPAYMENT_DEMO_MODE=true\n', encoding='utf-8')
    from config import Config
    from sqlalchemy.engine import make_url
    url = make_url(Config.SQLALCHEMY_DATABASE_URI)
    if url.host not in ('127.0.0.1', 'localhost'):
        raise RuntimeError('Use a local MySQL DATABASE_URL; remote initialization is refused.')
    if url.port == 3307 and not port_open(3307):
        exe = Path(os.environ.get('MYSQLD_PATH', r'C:\Program Files\MySQL\MySQL Server 8.0\bin\mysqld.exe'))
        if not exe.exists():
            raise RuntimeError('Install official MySQL Server 8.0 or set MYSQLD_PATH. See README.md.')
        datadir = LOCAL / 'mysql'
        if not (datadir / 'mysql').exists():
            subprocess.run([str(exe), '--no-defaults', '--initialize-insecure', f'--datadir={datadir}'], check=True)
        with (LOCAL / 'mysql.stdout.log').open('a') as out, (LOCAL / 'mysql.stderr.log').open('a') as err:
            subprocess.Popen([str(exe), '--no-defaults', f'--datadir={datadir}', '--port=3307', '--bind-address=127.0.0.1', '--mysqlx=0'], stdout=out, stderr=err, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        for _ in range(60):
            if port_open(3307):
                break
            time.sleep(.5)
    # Only initialize the isolated project instance, and only once.
    if url.port == 3307 and not (LOCAL / 'mysql.configured').exists():
        conn = pymysql.connect(host='127.0.0.1', port=3307, user='root', password='')
        with conn.cursor() as cur:
            cur.execute('SELECT @@datadir')
            actual=Path(cur.fetchone()[0]).resolve()
            expected=(LOCAL/'mysql').resolve()
            if str(actual).casefold()!=str(expected).casefold():
                conn.close()
                raise RuntimeError('Port 3307 belongs to another MySQL data directory. Nothing was changed.')
            cur.execute('CREATE DATABASE IF NOT EXISTS chaplin_demo CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci')
            cur.execute("CREATE USER IF NOT EXISTS 'chaplin'@'localhost' IDENTIFIED WITH mysql_native_password BY %s", (url.password,))
            cur.execute("GRANT ALL PRIVILEGES ON chaplin_demo.* TO 'chaplin'@'localhost'")
            root_password = secrets.token_hex(32)
            cur.execute("ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY %s", (root_password,))
        conn.close()
        (LOCAL / 'mysql-root.txt').write_text(root_password, encoding='utf-8')
        (LOCAL / 'mysql.configured').write_text('isolated instance configured', encoding='utf-8')
    from app import app
    from schema import initialize
    from seed_demo import seed
    with app.app_context():
        initialize()
        seed()
    print('MySQL ready. Open http://127.0.0.1:5000 — accounts: .local/demo-accounts.txt')

if __name__ == '__main__':
    main()
