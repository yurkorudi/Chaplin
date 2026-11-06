from flask import Flask
from extensions import db
from models import Image, User, Cinema, Session, Film, Seat, Ticket

app = Flask(__name__)

from config import Config
app.config.from_object(Config)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

@app.route('/')
def create_tables():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=False)
