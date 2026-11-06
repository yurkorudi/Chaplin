import pymysql
pymysql.install_as_MySQLdb()
from flask import *
from flask import session as flask_session
from user_agents import *
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from time import *
from flask_admin import Admin, BaseView, expose
from flask_admin.contrib.sqla import ModelView
from flask_admin.form import FileUploadField
from wtforms_sqlalchemy.fields import QuerySelectField
from flask_admin.form import SecureForm
from wtforms.validators import DataRequired
from flask_admin.model import filters
from flask_admin import helpers as admin_helpers
from flask_admin import AdminIndexView
from werkzeug.utils import secure_filename
from io import BytesIO
from flask import send_file
from io import BytesIO
from reportlab.lib.pagesizes import A6
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import mm
import os


from flask import Flask
from flask_admin import Admin, AdminIndexView, expose, BaseView
from flask_admin.contrib.sqla import ModelView
from flask_admin.form import SecureForm
from flask_admin.form import FileUploadField
from wtforms_sqlalchemy.fields import QuerySelectField
from werkzeug.utils import secure_filename



import hashlib

from apis import *
pdfmetrics.registerFont(
    TTFont('DejaVuSans', 'static/fonts/DejaVuSans.ttf'),
)
pdfmetrics.registerFont(
    TTFont('DejaVuSans-Bold', 'static/fonts/DejaVuSans-Bold.ttf')
)
pdfmetrics.registerFont(
    TTFont('DejaVuSans-BoldOblique', 'static/fonts/DejaVuSans-BoldOblique.ttf')
)
pdfmetrics.registerFont(
    TTFont('DejaVuSans-ExtraLight', 'static/fonts/DejaVuSans-ExtraLight.ttf')
)




from extensions import db
from models import Image, User, Cinema, Session, Film, Seat, Ticket, Hall
from sqlalchemy import func


from funcs import *
from modls import *

# import json
# import qrcode
# from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
# from reportlab.lib.styles import getSampleStyleSheet
# from reportlab.platypus import Table, TableStyle
# from reportlab.lib import colors


app = Flask(__name__)


from config import Config
app.config.from_object(Config)
if not app.config['SECRET_KEY']:
    raise RuntimeError('Missing SECRET_KEY. Run venv/Scripts/python.exe setup_local.py first.')

db.init_app(app)



#### ___________________________________admin______________________________________ ####

class CustomHomeView(AdminIndexView):
    @expose('/')
    def index(self):
        from models import Order
        from datetime import date
        stats = [('Фільми', Film.query.count()), ('Майбутні сеанси', Session.query.filter(Session.session_datetime > datetime.now()).count()), ('Продані квитки', Ticket.query.count()), ('Сплачені замовлення', Order.query.filter_by(status='paid').count())]
        return self.render('admin/dashboard.html', stats=stats, cinemas=Cinema.query.order_by(Cinema.city).all())

    def is_accessible(self):
        return flask_session.get('is_admin')


    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('admin_login'))



class AuthModelView(ModelView):
    # WTForms-SQLAlchemy 0.4 uses WTForms 3.2's four-part choice protocol.
    # Flask-Admin 1.6's bundled relationship fields still yield three parts.
    form_overrides = {name: QuerySelectField for name in ('cinema', 'hall', 'film', 'category')}
    from admin_forms import AdminForm
    form_base_class = AdminForm
    page_size = 25

    def is_accessible(self):
        return flask_session.get('is_admin')
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('admin_login'))

class FilmView(AuthModelView):
    form_overrides = {'image': QuerySelectField}
    column_searchable_list = ['name', 'genre']
    form_columns = [
        'name', 'genre', 'description',
        'release_start_date', 'release_end_date',
        'director', 'actors', 'duration', 'age', 'image'
    ]

    form_args = {
        'image': {
            'query_factory': lambda: Image.query.all(),
            'get_label': lambda i: i.path
        },
    }

    column_list = [
        'name', 'genre', 'director',
        'release_start_date'
    ]



class ImageView(AuthModelView):
    form_columns = ['type', 'path', 'upload']
    from wtforms.validators import Optional
    form_args = {'path': {'validators': [Optional()]}}
    from wtforms import FileField
    form_extra_fields = {'upload': FileField('Завантажити JPEG / PNG / WebP')}
    def on_model_change(self, form, model, is_created):
        from PIL import Image as PILImage
        import secrets
        upload = form.upload.data
        if upload and upload.filename:
            try:
                image = PILImage.open(upload.stream)
                image.verify()
                upload.stream.seek(0)
                image = PILImage.open(upload.stream)
                if image.format not in ('JPEG', 'PNG', 'WEBP') or image.width * image.height > 25000000:
                    raise ValueError('Використовуйте JPEG, PNG або WebP до 25 мегапікселів.')
                folder = os.path.join(app.root_path, 'static', 'uploads')
                os.makedirs(folder, exist_ok=True)
                filename = secrets.token_hex(12) + '.png'
                image.convert('RGB').save(os.path.join(folder, filename), format='PNG')
                model.path = '/static/uploads/' + filename
            except (OSError, PILImage.DecompressionBombError) as error:
                raise ValueError('Невірне зображення.') from error
        if not model.path or not model.path.startswith('/static/') or '..' in model.path:
            raise ValueError('Оберіть локальний шлях /static/ або завантажте зображення.')
        return super().on_model_change(form, model, is_created)


class SessionView(AuthModelView):
    form_columns = [
        'film',
        'cinema',
        'hall',
        'session_datetime',
        'session_duration'
    ]
    column_list = form_columns

    form_args = {
        'film': {
            'query_factory': lambda: Film.query.all(),
            'get_label': 'name'
        },
        'cinema': {
            'query_factory': lambda: Cinema.query.all(),
            'get_label': 'name'
        },
        'hall': {
            'query_factory': lambda: Hall.query.all(),
            'get_label': lambda h: f"{h.name} ({h.cinema.name})"
        }
    }
    form_ajax_refs = {
        'film':   {'fields': ['name']},
        'cinema': {'fields': ['name']},
        'hall':   {'fields': ['name']}
    }

class CinemaView(AuthModelView):
    form_columns = ['name', 'city', 'location', 'contact_phone_number', 'work_schedule', 'instagram_link']

class SessionView(AuthModelView):

    column_list = ['film', 'cinema', 'hall', 'session_datetime', 'session_duration', 'price']
    column_filters = ['cinema.city', 'cinema.name', 'hall.name']
    column_searchable_list = ['film.name']


    form_columns = ['film', 'cinema', 'hall', 'session_datetime', 'price', 'vip_multiplier']

    def on_model_change(self, form, model, is_created):
        model.session_duration = model.film.duration
        return super().on_model_change(form, model, is_created)


    form_overrides = {
        'film':   QuerySelectField,
        'cinema': QuerySelectField,
        'hall':   QuerySelectField,
    }


    form_args = {
        'film': {
            'query_factory': lambda: Film.query.all(),
            'get_label': 'name',
            'allow_blank': False
        },
        'cinema': {
            'query_factory': lambda: Cinema.query.all(),
            'get_label': 'name',
            'allow_blank': False
        },
        'hall': {
            'query_factory': lambda: Hall.query.all(),
            'get_label': lambda h: f"{h.name} ({h.cinema.name})",
            'allow_blank': False
        }
    }



class HollView(BaseView):
    @expose('/')
    def index(self, **kwargs):
        cinemas = (
            Cinema
            .query
            .options(db.joinedload(Cinema.halls))
            .order_by(Cinema.name)
            .all()
        )
        pass  # Diagnostic output removed: never log credentials or personal data.
        return self.render('holl/Holl.html', cinemas=cinemas)


class HallView(AuthModelView):
    form_columns = ['name', 'cinema', 'rows', 'columns', 'structure']
    column_list  = ['name', 'cinema', 'rows', 'columns']
    form_args = {
        'cinema': {
            'query_factory': lambda: Cinema.query.all(),
            'get_label': 'name'
        }
    }


class CinemaView(AuthModelView):
    form_columns = ['name', 'city', 'location', 'contact_phone_number', 'work_schedule', 'instagram_link']



class CustomHomeVievManager(AdminIndexView):
    @expose('/')
    def index(self, **kwargs):

        return self.render('manager/manager_home.html')

    def is_accessible(self):
        return flask_session.get('is_manager')


    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('admin_login'))


admin = Admin(
    app,
    name='Chaplin',
    template_mode='bootstrap3',
    base_template='admin/chaplin_base.html',
    index_view=CustomHomeView(url='/admin', endpoint='admin'),
    url='/admin',
)

admin.add_view(HollView(endpoint='holls', name='Геометрія залів'))
admin.add_view(CinemaView(Cinema, db.session, name='Кінотеатри'))
admin.add_view(HallView(Hall, db.session, name='Зали'))
admin.add_view(FilmView(Film, db.session, name='Фільми'))
admin.add_view(SessionView(Session, db.session, name='Сеанси'))
admin.add_view(ImageView(Image, db.session, name='Зображення'))

#### ___________________________________admin______________________________________ ####









pass  # Diagnostic output removed: never log credentials or personal data.
cities = []
user_location = []
user_device = 'None'



@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    from commerce import admin_login as handler
    return handler()

@app.route('/admin/logout')
def admin_logout():
    from commerce import admin_logout as handler
    return handler()

@app.route('/moder', methods=['GET', 'POST'])
def moder():
    from commerce import moder as handler
    return handler()

@app.route('/admin_tickets', methods=['GET', 'POST'])
def admin_tickets():
    from commerce import admin_tickets as handler
    return handler()


@app.route('/manager/login',  methods=['GET', 'POST'])
def manager_login():
    from commerce import manager_login as handler
    return handler()

@app.route('/manager/logout')
def manager_logout():
    from commerce import manager_logout as handler
    return handler()


@app.route('/')
def early_start ():
    global user_device
    return redirect(url_for('homepage'))



def location():
    global user_location
    global cities
    if user_location == []:
        pass  # Diagnostic output removed: never log credentials or personal data.
        location = request.args.get('location')
        city = ""
        if location:
            city = cities[location]
    return

# @app.route("/api/films")
# def get_films():
#     cinema_id = request.args.get('cinema_id')
#     films = Film.query.join(Hall).filter(Hall.cinema_id == cinema_id).all()
#     return jsonify([{
#         "id": f.id,
#         "title": f.title,
#         "hall_structure": f.hall.structure,

#     } for f in films])




@app.route('/api/halls/<int:hall_id>', methods=['PUT'])
def update_hall(hall_id):
    from commerce import update_hall as handler
    return handler(hall_id)

@app.route('/api/halls', methods=['POST'])
def create_hall():
    from commerce import create_hall as handler
    return handler()

@app.route("/api/save_hall_structure/<int:hall_id>", methods=["POST"])
def save_hall_structure(hall_id):
    from commerce import save_hall_structure as handler
    return handler(hall_id)


@app.route('/home')
def homepage():
    global user_location
    global cities
    global user_device

    ua_string = request.headers.get("User-Agent", "")
    user_agent = parse(ua_string)
    is_mobile = user_agent.is_mobile

    all_movies = get_films()
    allowed_ids = {sid for (sid,) in db.session.query(Session.film_id).join(Cinema).filter(Cinema.city == flask_session.get('city', 'Київ'), Session.session_datetime >= datetime.now()).distinct()}
    all_movies = [f for f in all_movies if f['film_id'] in allowed_ids]
    all_images = get_images()
    city = session.get('city', 'Київ')
    profile = session.get('user', "")
    pass  # Diagnostic output removed: never log credentials or personal data.
    pass  # Diagnostic output removed: never log credentials or personal data.
    for a in all_movies:
        for i in all_images:
            if a['image_id'] == i['id']:
                a.update({'img_src': i['path']})

    from sqlalchemy import cast, DateTime
    selected_city = flask_session.get('city', 'Київ')

    films = (
        db.session.query(Film, Session)
        .join(Session, Session.film_id == Film.film_id)
        .join(Cinema, Session.cinema_id == Cinema.cinema_id)
        .filter(
            func.date(Session.session_datetime) == datetime.now().date(),
            Cinema.city == selected_city,
            Session.session_datetime > datetime.now()
        )
        .order_by(Session.session_datetime)
        .limit(2)
        .all()
    )
    for a, s in films:
        for i in all_images:
            if a.image_id == i['id']:
                a.img_src = i['path']
        pass  # Diagnostic output removed: never log credentials or personal data.


    from models import Product
    featured_products = Product.query.filter_by(active=True).order_by(Product.id).limit(4).all()
    return render_template('Homepage.html', products=featured_products, city = city, cities = g.cities, mobile = is_mobile, movies = all_movies, profile = profile, nearest = films)



@app.route('/movies')
def movies():
    global user_location
    global user_device
    if user_location == []:
        a = location()
    all_movies = get_films()
    allowed_ids = {sid for (sid,) in db.session.query(Session.film_id).join(Cinema).filter(Cinema.city == flask_session.get('city', 'Київ'), Session.session_datetime >= datetime.now()).distinct()}
    all_movies = [f for f in all_movies if f['film_id'] in allowed_ids]
    all_images = get_images()
    for a in all_movies:
        for i in all_images:
            if a['image_id'] == i['id']:
                pass  # Diagnostic output removed: never log credentials or personal data.
                pass  # Diagnostic output removed: never log credentials or personal data.
                pass  # Diagnostic output removed: never log credentials or personal data.
                a.update({'img_src': i['path']})
                pass  # Diagnostic output removed: never log credentials or personal data.


    return render_template('Movies.html', city = "", cities = g.cities, movies = all_movies)



@app.route('/movie')
def movie():
    global user_location
    global user_device
    global json
    film_name = request.args.get('movie_name')
    film = Film.query.filter_by(name=film_name).first()

    sessions = []
    tickets_by_session = {}

    today = datetime.now().date()

    if film is None:
        abort(404)
    for s in film.sessions:
        if s.cinema.city != flask_session.get('city', 'Київ') or s.session_datetime <= datetime.now():
            continue
        if s.session_datetime.date() < today:
            continue
        if not s.hall:
            continue
        hall_obj = Hall.query.get(s.hall.id)
        cinema_obj = Cinema.query.get(s.cinema.cinema_id)
        sessions.append({
            'session_id':       s.session_id,
            'datetime':         s.session_datetime.isoformat(),
            'hall_id':          s.hall.id,
            'hall_name':        s.hall.name,
            'cinema_name':      s.cinema.name,
            'hall_structure':   hall_obj.structure,
            'price': float(s.price),
            'vip_multiplier': float(s.vip_multiplier),
            'city': cinema_obj.city
        })
        pass  # Diagnostic output removed: never log credentials or personal data.
        pass  # Diagnostic output removed: never log credentials or personal data.
        pass  # Diagnostic output removed: never log credentials or personal data.
        pass  # Diagnostic output removed: never log credentials or personal data.
        pass  # Diagnostic output removed: never log credentials or personal data.
        pass  # Diagnostic output removed: never log credentials or personal data.
        pass  # Diagnostic output removed: never log credentials or personal data.

        tickets = Ticket.query.filter_by(
            session_id=s.session_id
        ).all()
        from commerce import occupied_positions
        ticket_list = occupied_positions(s.session_id)
        tickets_by_session[s.session_id] = ticket_list

    pass  # Diagnostic output removed: never log credentials or personal data.

    today = datetime.now().date()

    daysUA = ['Нд', 'Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб']
    monthsUA = [
        'січня', 'лютого', 'березня', 'квітня', 'травня', 'червня', 'липня', 'серпня', 'вересня',
        'жовтня', 'листопада', 'грудня'
    ]

    unique_dates = sorted({
        datetime.fromisoformat(s['datetime']).date()
        for s in sessions
        if datetime.fromisoformat(s['datetime']).date() >= today
    })

    dates_for_dropdown = []

    for i, d in enumerate(unique_dates):
        day_abbr = daysUA[d.weekday()]
        month_name = monthsUA[d.month - 1]
        label = f"{day_abbr}, {d.day} {month_name}"

        if d == today:
            label += " — сьогодні"
        elif d == today + timedelta(days=1):
            label += " — завтра"

        dates_for_dropdown.append({
            'value': d.isoformat(),  # YYYY-MM-DD для value
            'label': label           # текст для dropdown
        })

    movie_info = {
        'film_id':             film.film_id,
        'name':                film.name,
        'genre':               film.genre,
        'description':         film.description,
        'release_start_date':  film.release_start_date,
        'release_end_date':    film.release_end_date,
        'director':            film.director,
        'actors':              film.actors,
        'duration':            film.duration,
        'age':                 film.age,
        'img_src':             film.image.path if film.image else None,
        'sessions':            sessions,
        'trailer':             film.trailer,
    }

    ua_string = request.headers.get("User-Agent", "")
    user_agent = parse(ua_string)
    is_mobile = user_agent.is_mobile

    return render_template('Movie.html',
                           movie_info=movie_info, sessions = sessions, tickets_by_session = tickets_by_session,
                           city="" , cities=g.cities, today=datetime.now(), timedelta=timedelta, dates=dates_for_dropdown,
                           mobile = is_mobile)



@app.route('/schedule')
def schedule():
    from commerce import schedule as handler
    return handler()


@app.route("/available-sessions", methods=["POST"])
def available_sessions():
    from commerce import available_sessions as handler
    return handler()


@app.route('/about')
def about():
    global user_location
    global cities
    global user_device

    ua_string = request.headers.get("User-Agent", "")
    user_agent = parse(ua_string)
    is_mobile = user_agent.is_mobile
    return render_template('about_live.html', cinemas=Cinema.query.filter_by(city=flask_session['city']).all())


@app.route('/book', methods=['GET', 'POST'])
def book():
    from commerce import book as handler
    return handler()


@app.route('/buy_ticket', methods=['POST'])
def buy_ticket():
    from commerce import buy_ticket as handler
    return handler()





@app.route('/ticket_confirmation', methods=['POST', 'GET'])
def ticket_confirmation():
    from commerce import ticket_confirmation as handler
    return handler()




@app.route('/ticket_pdf', methods=['GET'])
def ticket_pdf():
    from commerce import ticket_pdf as handler
    return handler()








@app.route('/user', methods=['GET', 'POST'])
def user():
    from commerce import user as handler
    return handler()


@app.route('/singup', methods=['GET', 'POST'])
def singup():
    from commerce import singup as handler
    return handler()



@app.route('/logout', methods=['GET', 'POST'])
def logout():
    from commerce import logout as handler
    return handler()


@app.route('/login', methods=['GET', 'POST'])
def login():
    from commerce import login as handler
    return handler()


@app.route('/user')
def button_click():
    global user_location
    global cities
    global user_device
    return render_template('User.html', city = "", cities = g.cities)

@app.route('/profile')
def profile():
    from commerce import profile as handler
    return handler()



@app.route('/set_city', methods=['POST'])
def set_city():
    from commerce import set_city as handler
    return handler()



@app.route('/market', methods=['POST', 'GET'])
def market():
    from commerce import market as handler
    return handler()








from commerce import install
install(app, admin, AuthModelView)

if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5000, debug=False, load_dotenv=False)
