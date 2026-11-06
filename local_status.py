"""Return 0 only when this project's healthy local website is already running."""
import json
from urllib.request import urlopen
from urllib.error import URLError

def running():
    try:
        with urlopen('http://127.0.0.1:5000/healthz',timeout=2) as response:
            result=json.load(response)
        return result.get('application')=='chaplin' and result.get('database')=='ok'
    except (URLError,OSError,ValueError):
        return False

if __name__=='__main__':
    raise SystemExit(0 if running() else 1)
