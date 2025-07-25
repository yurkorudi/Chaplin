from extensions import db
from datetime import datetime

class Image(db.Model):
    __tablename__ = 'images'
    image_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    type     = db.Column(db.String(50), nullable=False)
    path     = db.Column(db.String(50), unique=True, nullable=False)

class Cinema(db.Model):
    __tablename__ = 'cinemas'
    cinema_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name      = db.Column(db.String(100), nullable=False)
    location  = db.Column(db.String(200), nullable=False)
    contact_phone_number = db.Column(db.String(20))
    work_schedule        = db.Column(db.String(200))
    instagram_link       = db.Column(db.String(255))


    halls    = db.relationship('Hall',    back_populates='cinema', cascade='all, delete-orphan')
    sessions = db.relationship('Session', back_populates='cinema')
    users    = db.relationship('User',    back_populates='cinema')
    def __str__(self):
        return self.name

class Hall(db.Model):
    __tablename__ = 'halls'
    id        = db.Column(db.Integer, primary_key=True)
    name      = db.Column(db.String(100), nullable=True)    
    cinema_id = db.Column(db.Integer, db.ForeignKey('cinemas.cinema_id'), nullable=False)
    rows      = db.Column(db.Integer, nullable=False)
    columns   = db.Column(db.Integer, nullable=False)
    structure = db.Column(db.JSON,    nullable=False)

    cinema = db.relationship('Cinema', back_populates='halls')
    sessions = db.relationship('Session', back_populates='hall')
    def __str__(self):
        return self.name

class Film(db.Model):
    __tablename__ = 'films'
    film_id            = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name               = db.Column(db.String(300), nullable=False)
    genre              = db.Column(db.String(50))
    description        = db.Column(db.Text)
    release_start_date = db.Column(db.Date)
    release_end_date   = db.Column(db.Date)
    director           = db.Column(db.String(100))
    actors             = db.Column(db.Text)
    duration           = db.Column(db.Integer, nullable=False)
    age                = db.Column(db.String(100))
    image_id           = db.Column(db.Integer, db.ForeignKey('images.image_id'), nullable=True)
    
    def __str__(self):
        return self.name


    image    = db.relationship('Image')
    sessions = db.relationship('Session', back_populates='film')

class Session(db.Model):
    __tablename__ = 'sessions'
    session_id       = db.Column(db.Integer, primary_key=True, autoincrement=True)
    film_id          = db.Column(db.Integer, db.ForeignKey('films.film_id'), nullable=False)
    cinema_id        = db.Column(db.Integer, db.ForeignKey('cinemas.cinema_id'), nullable=False)
    hall_id          = db.Column(db.Integer, db.ForeignKey('halls.id'), nullable=True)
    session_datetime = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    session_duration = db.Column(db.Integer,  nullable=False)

    film   = db.relationship('Film',   back_populates='sessions')
    cinema = db.relationship('Cinema', back_populates='sessions')
    hall   = db.relationship('Hall',   back_populates='sessions')
    seats  = db.relationship('Seat',    back_populates='session')
    tickets= db.relationship('Ticket',  back_populates='session')

class User(db.Model):
    __tablename__ = 'users'
    id                     = db.Column(db.Integer, primary_key=True, autoincrement=True)
    first_name             = db.Column(db.String(50), nullable=False)
    last_name              = db.Column(db.String(50), nullable=False)
    email                  = db.Column(db.String(100), unique=True, nullable=False)
    login                  = db.Column(db.String(100), unique=True, nullable=False)
    password               = db.Column(db.String(500), nullable=False)
    date_of_creation       = db.Column(db.Date, default=datetime.utcnow, nullable=False)
    bought_tickets_summary = db.Column(db.Integer, nullable=False)
    cinema_id              = db.Column(db.Integer, db.ForeignKey('cinemas.cinema_id'))
    image_id               = db.Column(db.Integer, db.ForeignKey('images.image_id'))

    cinema = db.relationship('Cinema', back_populates='users')
    image  = db.relationship('Image')

class Seat(db.Model):
    __tablename__ = 'seats'
    seat_id    = db.Column(db.Integer, primary_key=True, autoincrement=True)
    session_id = db.Column(db.Integer, db.ForeignKey('sessions.session_id'), nullable=False)
    row        = db.Column(db.Integer, nullable=False)
    busy       = db.Column(db.Boolean, default=False)

    session = db.relationship('Session', back_populates='seats')

class Ticket(db.Model):
    __tablename__ = 'tickets'
    ticket_id        = db.Column(db.Integer, primary_key=True, autoincrement=True)
    date_of_purchase = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    seat_id          = db.Column(db.Integer, db.ForeignKey('seats.seat_id'), nullable=False)
    session_id       = db.Column(db.Integer, db.ForeignKey('sessions.session_id'), nullable=False)
    cost             = db.Column(db.Integer, nullable=False)
    user_id          = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    row_index        = db.Column(db.Integer, nullable=False)
    column_index     = db.Column(db.Integer, nullable=False)
    cinema_id        = db.Column(db.String(100))
    sell_type        = db.Column(db.String(45)) 
    seat    = db.relationship('Seat')
    session = db.relationship('Session', back_populates='tickets')
    user    = db.relationship('User')
