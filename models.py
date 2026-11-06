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
    city                 = db.Column(db.String(45))


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
    trailer            = db.Column(db.String(500))

    
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
    price = db.Column(db.Numeric(10, 2), nullable=False, default=150)
    vip_multiplier = db.Column(db.Numeric(4, 2), nullable=False, default=1.5)

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
    phone = db.Column(db.String(25))
    role = db.Column(db.String(20), nullable=False, default='customer')

    cinema = db.relationship('Cinema', back_populates='users')
    image  = db.relationship('Image')

class Seat(db.Model):
    __tablename__ = 'seats'
    seat_id    = db.Column(db.Integer, primary_key=True, autoincrement=True)
    session_id = db.Column(db.Integer, db.ForeignKey('sessions.session_id'), nullable=False)
    row        = db.Column(db.Integer, nullable=False)
    busy       = db.Column(db.Boolean, default=False)
    column_index = db.Column(db.Integer, nullable=True)
    __table_args__ = (db.UniqueConstraint('session_id', 'row', 'column_index', name='uq_seat_position'),)

    session = db.relationship('Session', back_populates='seats')

class Ticket(db.Model):
    __tablename__ = 'tickets'
    ticket_id        = db.Column(db.Integer, primary_key=True, autoincrement=True)
    date_of_purchase = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    seat_id          = db.Column(db.Integer, db.ForeignKey('seats.seat_id'), nullable=False)
    session_id       = db.Column(db.Integer, db.ForeignKey('sessions.session_id'), nullable=False)
    cost             = db.Column(db.Numeric(10, 2), nullable=False)
    user_id          = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    row_index        = db.Column(db.Integer, nullable=False)
    column_index     = db.Column(db.Integer, nullable=False)
    cinema_id        = db.Column(db.String(100))
    sell_type        = db.Column(db.String(45)) 
    order_id = db.Column(db.String(36), db.ForeignKey('orders.id'), nullable=True, index=True)
    token = db.Column(db.String(64), unique=True, nullable=True)
    __table_args__ = (db.UniqueConstraint('session_id', 'row_index', 'column_index', name='uq_ticket_position'),)
    seat    = db.relationship('Seat')
    session = db.relationship('Session', back_populates='tickets')
    user    = db.relationship('User')

class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.String(36), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    kind = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending', index=True)
    total = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(3), nullable=False, default='UAH')
    payment_method = db.Column(db.String(20), nullable=False, default='online')
    fulfillment = db.Column(db.String(20))
    fulfillment_status = db.Column(db.String(20),nullable=False,default='pending')
    delivery = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    expires_at = db.Column(db.DateTime, index=True)
    paid_at = db.Column(db.DateTime)
    fiscal_status = db.Column(db.String(30), nullable=False, default='not_fiscalized')
    is_demo = db.Column(db.Boolean, nullable=False, default=False)
    items = db.relationship('OrderItem', backref='order', lazy='selectin')
    tickets = db.relationship('Ticket', backref='order', lazy='selectin')

    @property
    def is_expired(self):
        return self.status=='pending' and self.expires_at is not None and self.expires_at<=datetime.now()

class OrderItem(db.Model):
    __tablename__ = 'order_items'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.String(36), db.ForeignKey('orders.id'), nullable=False, index=True)
    session_id = db.Column(db.Integer, db.ForeignKey('sessions.session_id'))
    seat_id = db.Column(db.Integer, db.ForeignKey('seats.seat_id'))
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))
    row_index = db.Column(db.Integer)
    column_index = db.Column(db.Integer)
    name = db.Column(db.String(300), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    session = db.relationship('Session')
    product = db.relationship('Product')

    def __str__(self):
        return f'{self.name} × {self.quantity} / {self.price} UAH'

class SeatReservation(db.Model):
    __tablename__ = 'seat_reservations'
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('sessions.session_id'), nullable=False)
    row_index = db.Column(db.Integer, nullable=False)
    column_index = db.Column(db.Integer, nullable=False)
    order_id = db.Column(db.String(36), db.ForeignKey('orders.id'), nullable=False, index=True)
    expires_at = db.Column(db.DateTime, nullable=False, index=True)
    __table_args__ = (db.UniqueConstraint('session_id', 'row_index', 'column_index', name='uq_reservation_position'),)

class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    def __str__(self):
        return self.name

class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False, unique=True)
    description = db.Column(db.Text)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False, index=True)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    stock = db.Column(db.Integer, nullable=False, default=0)
    image = db.Column(db.String(255), default='/static/img/merch.svg')
    active = db.Column(db.Boolean, nullable=False, default=True)
    category = db.relationship('Category')
    __table_args__ = (db.CheckConstraint('stock >= 0', name='ck_product_stock'), db.CheckConstraint('price >= 0', name='ck_product_price'))
    def __str__(self):
        return self.name

class PaymentReceipt(db.Model):
    """Minimal verified payment evidence; no card details or callback secrets."""
    __tablename__ = 'payment_receipts'
    id = db.Column(db.Integer,primary_key=True)
    order_id = db.Column(db.String(36),db.ForeignKey('orders.id'),nullable=False,unique=True)
    provider_reference = db.Column(db.String(100),nullable=False,unique=True)
    amount = db.Column(db.Numeric(10,2),nullable=False)
    currency = db.Column(db.String(3),nullable=False)
    status = db.Column(db.String(30),nullable=False)
    received_at = db.Column(db.DateTime,nullable=False,default=datetime.utcnow)
