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


from funcs import *
from modls import *



app = Flask(__name__)


app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://rootforchaplin:Super_Password22@167.172.62.229:3306/ChaplinDB"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config['SECRET_KEY'] = 'AdminSecretKey(2025)s'
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['JSON_AS_ASCII'] = False
app.config['ADMIN_PASSWORD'] = os.environ.get('ADMIN_PASSWORD', 'supersecret123')
app.config['MODERATOR_PASSWORD'] = os.environ.get('MODERATOR_PASSWORD', '1')
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"


GOOGLE_MAPS_API_KEY = 'AIzaSyCL1RYn2TgJBFu-7Vne8tdJBKc6v6GCzpM'

db.init_app(app)



#### ___________________________________admin______________________________________ ####

ACCESS_PASSWORDS = {
    "superadmin": "super123",
    "admin": "admin456",
    "moderator": "mod789"
}


class CustomHomeView(AdminIndexView):
    @expose('/')
    def index(self):
        cinemas_stats = [
            {
                'name': 'Кінотеатр А',
                'tickets_today': 120,
                'total_income': 15000,
                'sessions_today': 10,
                'visitors_today': 300,
            },
            {
                'name': 'Кінотеатр Б',
                'tickets_today': 90,
                'total_income': 11000,
                'sessions_today': 8,
                'visitors_today': 220,
            }
        ]
        return self.render('home/Home.html', cinemas=cinemas_stats)
    
    def is_accessible(self):
        return flask_session.get('is_admin')
    
    
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('admin_login'))



class AuthModelView(ModelView):
    def is_accessible(self):
        return flask_session.get('is_admin')
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('admin_login'))

class FilmView(ModelView):
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



class ImageView(ModelView):
    form_base_class = SecureForm
    form_overrides = {
        'path': FileUploadField
    }
    form_args = {
        'path': {
            'base_path': app.config['UPLOAD_FOLDER'] 
        }
    }

    def on_model_change(self, form, model, is_created):
        if form.path.data:
            filename = secure_filename(form.path.data.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            form.path.data.save(filepath)
            model.path = filepath
        return super(ImageView, self).on_model_change(form, model, is_created)


class SessionView(ModelView):
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

class CinemaView(ModelView):
    form_columns = ['name', 'location', 'contact_phone_number', 'work_schedule', 'instagram_link']

class SessionView(ModelView):

    column_list = ['film', 'cinema', 'hall', 'session_datetime', 'session_duration']


    form_columns = ['film', 'cinema', 'hall', 'session_datetime', 'session_duration']


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
        print("Cinemas with halls:", cinemas)
        return self.render('holl/Holl.html', cinemas=cinemas)
    
    
class HallView(ModelView):
    form_columns = ['name', 'cinema', 'rows', 'columns', 'structure']
    column_list  = ['name', 'cinema', 'rows', 'columns']
    form_args = {
        'cinema': {
            'query_factory': lambda: Cinema.query.all(),
            'get_label': 'name'
        }
    }
    
    
class CinemaView(ModelView):
    form_columns = ['name', 'location', 'contact_phone_number', 'work_schedule', 'instagram_link']
    
    
    
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
    name='My Admin',
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

with app.app_context():
    print(list_to_dict(get_users()))

def create_sample_data():
    with app.app_context():
        add_image(type="Poster", path="./static/img/photo1.jpg")
        add_image(type="Poster", path="./static/img/venomposter.jpg")
        add_image(type="Poster", path="./static/img/robotposter.jpg")
        add_image(type="Poster", path="./static/img/redposter.jpg")
        add_image(type="Poster", path="./static/img/buchaposter.jpg")
        add_image(type="Poster", path="./static/img/gladiatorposter.jpg")
        add_image(type="Poster", path="./static/img/poster07.jpg")
        add_image(type="Poster", path="./static/img/wickedposter.jpg")

        add_film(name="Трансформери: повернення", genre="Екшн, Пригоди, Фантастика", 
                 description="Фільм 'Трансформери' розповідає про те, як багато століть ведеться війна між двома расами роботів-інопланетян - Автоботами і Десептиконами, ставка в якій - доля Всесвіту. До Землі теж дійшла черга, війна не минула її стороною. Ключ до верховної влади є останньою надією на порятунок. У той час як зло намагається його відшукати, ключ знаходиться в руках у юного землянина. Найпростіший хлопчина Сем Уітвіккі, як і всі підлітки його віку живе звичайним життям: ходить в школу, зустрічається з друзями, захоплюється машинами та дівчатками. Він не підозрює, що він насправді - єдиний шанс на порятунок всього людства. Разом зі своєю подружкою Мікаелою, Сем виявляється в центрі війни трансформерів і розуміє про що говорить сімейний девіз - 'Без жертв перемоги немає!'.",
                release_start_date=datetime(2023, 5, 1), release_end_date=datetime(2023, 7, 1), 
                director="Рідлі Скотт",
                actors="Шайа Лабаф, Меґан Фокс, Джош Дюамель, Тайріз Гібсон, Рейчел Тейлор, Ентоні Андерсон", 
                duration=148, age='3+', image_id=1)
        add_film(name="Веном 3", genre="Фантастика, Екшн, Marvel", 
                 description="Фільм 'Веном 3' розповідає про повернення симбіота, який стикається з новими викликами та ворогами у світі Marvel.",
                release_start_date=datetime(2023, 6, 1), release_end_date=datetime(2023, 8, 1), 
                director="Келлі Марсел",
                actors="Том Харді, Чиветел Еджіофор, Джуно Темпл", duration=109, age='16+', image_id=2)
        add_film(name="Дикий робот", genre="Пригоди, Анімація", 
                 description="DreamWorks Animation представляє нову захопливу анімаційну пригоду за мотивами літературного бестселера! Епічна пригода про мандрівку робота ROZZUM 7134, скорочено «Роз», що зазнала корабельної аварії на безлюдному острові. Тепер їй доведеться пристосуватися до суворих умов навколишнього середовища, поступово налагодити стосунки з тваринами на острові та навіть замінити батьків осиротілому гусеняті.",
                release_start_date=datetime(2023, 7, 1), release_end_date=datetime(2023, 9, 1), 
                director="Кріс Сандерс",
                actors="Лупіта Ніонго, Педро Паскаль, Кетрін О'Хара, Біл Найї, Стефані Сюй", 
                duration=100, age='0+', image_id=3)
        add_film(name="Кодове імя: червоний", genre="Пригоди, Екшн, Комедія", 
                 description="Комедійний екшн-фільм 'Червоний Один', у якому група героїв вирушає на епічну місію.",
                release_start_date=datetime(2023, 8, 1), release_end_date=datetime(2023, 10, 1), 
                director="Джейк Кездан",
                actors="Двейн Джонсон, Кріс Еванс, Люсі Лю, Кірнан Шипка, Бонні Хант", duration=123, age='16+', image_id=4)
        add_film(name="Буча", genre="Історичний, Військовий, Драма", 
                 description="Фільм 'Буча' висвітлює героїчні події, засновані на реальних історичних подіях та життєвих драматичних поворотах.",
                release_start_date=datetime(2023, 5, 1), release_end_date=datetime(2023, 7, 1), 
                director="Станіслав Тіунов",
                actors="Цезарій Лукашевич, Вячеслав Довженко, Анастасія Нестеренко", 
                duration=118, age='16+', image_id=5)
        add_film(name="Гладіатор ІІ", genre="Історичний, Епічна історія", 
                 description="Від легендарного режисера Рідлі Скотта, «Гладіатор II» продовжує епічну сагу про владу, помсту та інтриги, події якої відбуваються в Стародавньому Римі. Декілька років тому Луцій став свідком вбивства Максимуса від рук свого дядька. Тепер він змушений увійти в Колізей після того як його дім було зруйновано імператорами-тиранами, які тепер керують Римом. Оскільки на карту поставлено майбутнє імперії, Луцій повинен знайти у собі сили забути минуле та повернути Риму і його народу колишню славу.",
                release_start_date=datetime(2023, 6, 1), release_end_date=datetime(2023, 8, 1), 
                director="Рідлі Скотт",
                actors="Пол Мескаль, Педро Паскаль, Дензел Вашингтон", duration=165, age='12+', image_id=6)
        add_film(name="Божевільні", genre="Трилер, Драма", 
                 description="Напружений трилер 'Божевільні' розкриває драматичні події в житті головних героїв, занурюючи глядачів у світ психологічних випробувань.",
                release_start_date=datetime(2023, 7, 1), release_end_date=datetime(2023, 9, 1), 
                director="Денис Тарасов",
                actors="Костянтин Темляк, Ірма Вітовська, Сергій Калантай", duration=120, age='18+', image_id=7)
        add_film(name="Чародійка", genre="Пригоди, Фентезі, Фантастика, Мюзикл", 
                 description="Нерозказана історія про відьом країни Оз у фільмі 'Wicked' зіграла лауреатка премій 'Еммі', 'Греммі' та 'Тоні' Синтія Еріво (Гаррієт, бродвейський мюзикл 'Пурпурний колір') у ролі Ельфаби - молодої жінки, яку не розуміють через її незвичний зелений колір шкіри, але якій ще належить відкрити свою справжню силу, та володарка 'Греммі', мультиплатинова артистка, світова суперзірка Аріана Гранде у ролі Глінди - популярної молодої дівчини, окутаної позолотою привілеїв і амбіцій, яка ще не відкрила свого істинного серця. Вони зустрічаються як студенти університету Шиз у фантастичній Країні Оз і зав'язують несподівану, але глибоку дружбу. Після зустрічі з Чудовим Чарівником Країни Оз їхня дружба виходить на перехрестя, і їхні життя розходяться в різні боки. Непохитне прагнення Глінди до популярності спокушає її владою, тоді як рішучість Ельфаби залишатися вірною собі та тим, хто її оточує, матиме несподівані й шокуючі наслідки для її майбутнього. Їхні надзвичайні пригоди в Країні Оз врешті-решт призведуть до того, що вони виконають свої долі Глінди Доброї та Злої Відьми Заходу.",
                release_start_date=datetime(2023, 8, 1), release_end_date=datetime(2023, 10, 1), 
                director="Джон М. Чу",
                actors="Cynthia Erivo, Ariana Grande, Jonathan Bailey, Marissa Bode, Ethan Slater, Michelle Yeoh, Jeff Goldblum, Keala Settle", 
                duration=150, age='3+', image_id=8)

        add_cinema(name="Grand Cinema", location="123 Main St, Cityville",
                contact_phone_number="555-1234", work_schedule="10:00 AM - 11:00 PM", instagram_link="https://instagram.com/grandcinema")
        add_cinema(name="Elite Theaters", location="456 Broadway Ave, Metropolis",
                contact_phone_number="555-5678", work_schedule="9:00 AM - 12:00 AM", instagram_link="https://instagram.com/elitetheaters")
        add_cinema(name="Movie Palace", location="789 Oak Lane, Smalltown",
                contact_phone_number="555-9012", work_schedule="11:00 AM - 10:00 PM", instagram_link="https://instagram.com/moviepalace")
        add_cinema(name="Galaxy Screens", location="101 Star Rd, Universe City",
                contact_phone_number="555-3456", work_schedule="8:00 AM - 1:00 AM", instagram_link="https://instagram.com/galaxyscreens")


        add_user(first_name="John", last_name="Doe",
                email="john.doe@example.com", login="johndoe", password="password123", bought_tickets_summary=3)
        add_user(first_name="Jane", last_name="Smith",
                email="jane.smith@example.com", login="janesmith", password="password456", bought_tickets_summary=5)
        add_user(first_name="Alice", last_name="Brown",
                email="alice.brown@example.com", login="alicebrown", password="password789", bought_tickets_summary=1)
        add_user(first_name="Bob", last_name="Johnson",
                email="bob.johnson@example.com", login="bobjohnson", password="password101", bought_tickets_summary=2)


        add_session(film_id=1, cinema_id=1, session_datetime=datetime(2023, 5, 10, 18, 0), session_duration=120)
        add_session(film_id=2, cinema_id=2, session_datetime=datetime(2023, 6, 15, 20, 0), session_duration=110)
        add_session(film_id=3, cinema_id=3, session_datetime=datetime(2023, 7, 20, 19, 0), session_duration=100)
        add_session(film_id=4, cinema_id=4, session_datetime=datetime(2023, 8, 25, 21, 0), session_duration=130)


        add_seat(session_id=1, row=1, busy=False)
        add_seat(session_id=1, row=2, busy=True)
        add_seat(session_id=2, row=1, busy=False)
        add_seat(session_id=2, row=2, busy=True)


        add_ticket(user_phone_number="1234567890", seat_id=1, session_id=1, user_id = 1)
        add_ticket(user_phone_number="0987654321", seat_id=2, session_id=1, user_id = 2)
        add_ticket(user_phone_number="1122334455", seat_id=3, session_id=2, user_id = 3)
        add_ticket(user_phone_number="5566778899", seat_id=4, session_id=2, user_id = 4)
    print("created!")







with app.app_context():
    cities = Cinema.query.with_entities(Cinema.city).all()
    cities = [city[0] for city in cities if city[0] is not None]
print('____________________________________________________________________ \n \n \n')
print("Cities from DB:", cities)
user_location = []
user_device = 'None'



@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        pwd = request.form.get('password')
        if pwd == app.config['ADMIN_PASSWORD']:
            flask_session['is_admin'] = True
            return redirect(url_for('admin.index'))
        elif pwd == ACCESS_PASSWORDS['moderator']:
            flask_session['is_manager'] = True
            return redirect(url_for('manager.index'))
        flash('Невірний пароль', 'error')
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    flask_session.pop('is_admin', None)
    return redirect(url_for('admin_login'))

@app.route('/moder', methods=['GET', 'POST'])
def moder():
    if not flask_session.get('is_moderator'):
        return redirect(url_for('manager_login'))
    if session['city']:
        try:
            cinema = Cinema.query.filter_by(city=session['city']).first()
            hall_structure = Hall.query.filter_by(cinema_id=cinema.id).first()
            return render_template('manager/manager_home.html', structure=hall_structure)
        except Exception as e:
            return render_template('manager/manager_home.html')

@app.route('/admin_tickets', methods=['GET', 'POST'])
def admin_tickets():
    print("Tickets")


@app.route('/manager/login',  methods=['GET', 'POST'])
def manager_login():
    if request.method == 'POST':
        pwd = request.form.get('password')
        if pwd == app.config['MODERATOR_PASSWORD']:
            flask_session['is_moderator'] = True
            return redirect(url_for('moder'))
        flash('Невірний пароль', 'error')
    return render_template('moder_login.html')

@app.route('/manager/logout')
def manager_logout():
    flask_session.pop('is_moderator', None)
    return redirect(url_for('manager_login'))


@app.route('/')
def early_start ():
    global user_device
    return redirect(url_for('homepage'))



def location():
    global user_location
    global cities
    if user_location == []:
        print("===", request.args)
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
    data = request.get_json() or {}

    hall = Hall.query.get(hall_id)
    if hall is None:
        abort(404, description=f"Hall {hall_id} not found")


    if 'structure' in data:
        hall.structure = data['structure']

    if 'rows' in data:
        hall.rows = data['rows']
    if 'columns' in data:
        hall.columns = data['columns']


    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


    return jsonify({
        "id": hall.id,
        "rows": hall.rows,
        "columns": hall.columns,
        "structure": hall.structure
    }), 200

@app.route('/api/halls', methods=['POST'])
def create_hall():
    data = request.get_json() or {}
    cinema_id = data.get('cinema_id')
    rows = data.get('rows')
    cols = data.get('columns')
    structure = data.get('structure') or [[1]*cols for _ in range(rows)]

    print("Отримані дані:", data)

    if not cinema_id or not rows or not cols:
        return jsonify({"error": "cinema_id, rows та columns мають бути в тілі запиту"}), 400

    hall = Hall(cinema_id=cinema_id, rows=rows, columns=cols, structure=structure)

    db.session.add(hall)
    try:
        db.session.commit()
        print("Зал успішно створено:", hall.id)
    except Exception as e:
        db.session.rollback()
        print("Помилка при створенні залу:", e)
        return jsonify({"error": str(e)}), 500

    return jsonify({"id": hall.id}), 201

@app.route("/api/save_hall_structure/<int:hall_id>", methods=["POST"])
def save_hall_structure(hall_id):
    structure = request.get_json()

    hall = json.dumps(structure)
    print("Saving hall structure for hall_id:", hall_id)
    print("Received hall structure:", hall)

    return jsonify({"status": "ok"})


@app.route('/home')
def homepage():
    global user_location
    global cities
    global user_device
    
    ua_string = request.headers.get("User-Agent", "")
    user_agent = parse(ua_string)    
    is_mobile = user_agent.is_mobile

    all_movies = get_films()
    all_images = get_images()
    city = session.get('city', "")
    profile = session.get('user', "")
    print("__________________________________________ profile __________________________________________")
    print("User profile in session:", profile)
    for a in all_movies:
        for i in all_images:
            if a['image_id'] == i['id']:
                a.update({'img_src': i['path']})

    return render_template('Homepage.html', city = city, cities = cities, mobile = is_mobile, movies = all_movies, profile = profile)



@app.route('/movies')
def movies():
    global user_location
    global user_device
    if user_location == []:
        a = location()
    all_movies = get_films()
    all_images = get_images()
    for a in all_movies:
        for i in all_images:
            if a['image_id'] == i['id']:
                print(a['image_id'])
                print(i['id'])
                print('___________________________________________________________________________________')
                a.update({'img_src': i['path']})
                print(a['img_src'])
    

    return render_template('Movies.html', city = "", cities = cities, movies = all_movies)
    


@app.route('/movie')
def movie():
    global user_location
    global user_device
    global json
    film_name = request.args.get('movie_name')
    film = Film.query.filter_by(name=film_name).first()
    
    sessions = []
    for s in film.sessions:
        if not s.hall:
            continue
        hall_obj = Hall.query.get(s.hall.id)
        sessions.append({
            'session_id':       s.session_id,
            'datetime':         s.session_datetime.isoformat(),
            'hall_id':          s.hall.id,
            'hall_name':        s.hall.name,
            'hall_structure':   hall_obj.structure
        })
        print("____________________________________________________________________________________")
        print("Session ID:", s.session_id)
        print("Session datetime:", s.session_datetime)
        print("Hall ID:", s.hall.id)
        print("Hall name:", s.hall.name)
        print("Hall structure:", hall_obj.structure)
        print("____________________________________________________________________________________")
        
    print("Sessions for film:", film_name, "are", sessions)
        
        
        
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
    }

    return render_template('Movie.html',
                           movie_info=movie_info,
                           city="" , cities=cities)


        




@app.route('/about')
def about():
    global user_location
    global cities
    global user_device
    return render_template('About.html', city = "", cities = cities)


@app.route('/book', methods=['GET', 'POST'])
def book():

    film_name = request.args.get('movie_name')
    data = request.form.get("selectedSeats")

    try:
        seat_details = json.loads(data)
        for seat in seat_details:
            seat_number = seat.get("seatNumber")
            row = seat.get("row")
            cost = seat.get("cost")
            print(f"Seat: {seat_number} in row {row} costs {cost}")
    except Exception as e:
        print("Error parsing seats:", e)

    fake_structure = [
        [1, 1, 1, 1, 1, 0],
        [1, 1, 1, 1, 1, 1],
        [1, 1, 2, 2, 1, 1]
    ]

    film = Film_obj(film_name)
    print("____________________________________________________________________")
    print("film.data:", film.data)
    print(film.data['sessions'])
    sessions_data = []
    for i in film.data['sessions']:
        hhall = Hall.query.filter_by(id=i['hall_id']).first()
        a = {
            'session_id': i['session_id'],
            'datetime': i['datetime'],
            'hall': {
                'name': i['hall_name'],
                'structure': hhall.structure if hhall else fake_structure
            }
        }
        sessions_data.append(a)
        
        
        
    film.data['sessions'] = sessions_data
    occupied_seats = {}

    for sess in film.data['sessions']:
        sid = sess['session_id']
        occupied_seats[sid] = []

        tickets = Ticket.query.filter_by(session_id=sid).all()
        for t in tickets:
            occupied_seats[sid].append({
                'row':        t.row_index,
                'seatNumber': t.column_index
            })
    print("____________________________________________ occupied_seats ___________________________________________")
    print("Occupied seats:", occupied_seats)
    
    
    return render_template(
        'Booking.html',
        city="",
        cities=cities,
        movie_info=film.data,
        occupied_seats=occupied_seats,
    )


@app.route('/buy_ticket', methods=['POST'])
def buy_ticket():
    print("___________________________________________ buy_ticket ___________________________________________")
    try:
        
        print("Raw Request Data:", request.data)
        
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "Empty or invalid JSON received EMPTYYYYYYYYY"}), 400
        
        print("Request JSON (parsed):", data)
        session_id = data.get('session_id')
        tickets = data.get('tickets')
        info = []
        if not session_id or not tickets:
            return jsonify({"error": "Session ID and tickets are required"}), 400
        
        
        if flask_session.get('user') is None:
            redirect_url = url_for('login')
            

        
        for i in tickets: 
            session = Session.query.filter_by(session_id=session_id).first()
            new_ticket = Ticket(
                seat_id = 1,
                session_id = session_id,
                user_id = User.query.filter_by(login=flask_session['user']).first().id, 
                cost = i['cost'],
                sell_type = 'online',
                cinema_id = session.cinema_id,
                row_index = i['row'],
                column_index = i['seatNumber']
            )
            db.session.add(new_ticket)
        
        
        db.session.commit()
        
        flask_session['confirmation_data'] = payload = {
            "session_id": session_id,
            "movie_name": Film.query.filter_by(film_id=session.film_id).first().name,
            "movie_details": 'b',
            "tickets":    tickets,
            "user": flask_session.get('user')
        }
        
        print(flask_session['confirmation_data'])
            
        return redirect(url_for('ticket_confirmation'))
    except Exception as e:
        print("Error in buy_ticket:", e)
        return jsonify({"error": "An error occurred while processing the request"}), 500
        




@app.route('/ticket_confirmation', methods=['POST', 'GET'])
def ticket_confirmation():
    print("___________________________________________ ticket_confirmation ___________________________________________")
    # data = request.get_json(force=True)
    # session_id = data.get('session_id')
    # tickets = data.get('tickets')
    
    data = flask_session.get('confirmation_data', None)
    
    print("Raw Request Data:", data)
    
    return render_template('TicketConfirmation.html',)




@app.route('/ticket_pdf', methods=['GET'])
def ticket_pdf():
    from io import BytesIO
    from flask import send_file, session as flask_session
    from reportlab.lib.pagesizes import A6
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import mm
    from models import Session as DBSess, Film as DBFilm, User as DBUser


    data = flask_session.get('confirmation_data')
    if not data:
        return "Немає даних квитка", 400


    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A6)
    width, height = A6


    banner_h = 8 * mm
    p.setFillColorRGB(129, 0, 0)
    p.rect(0, height - banner_h, width, banner_h, fill=1, stroke=0)

    margin_x = 6 * mm
    header_bottom = height - banner_h - 2 * mm


    film = DBFilm.query.filter_by(name=data['movie_name']).first()
    poster_path = film.image.path if film and film.image else 'static/img/default_poster.png'
    poster_w = 30 * mm
    poster_h = 40 * mm
    p.drawImage(
        poster_path,
        margin_x,
        header_bottom - poster_h,
        width=poster_w,
        height=poster_h,
        mask='auto'
    )


    title_x = margin_x + poster_w + 3 * mm
    title_y = header_bottom - 3 * mm
    p.setFillColorRGB(0, 0, 0)
    p.setFont("DejaVuSans-Bold", 10)
    p.drawString(title_x, title_y, data['movie_name'])

    y = header_bottom - poster_h - 6 * mm
    p.setFont("DejaVuSans", 6)
    p.drawString(margin_x, y, f"Куплено користувачем: {DBUser.query.filter_by(login=data.get('user', '')).first().first_name} {DBUser.query.filter_by(login=data.get('user', '')).first().last_name}")
    y -= 6 * mm

    sess = DBSess.query.filter_by(session_id=data['session_id']).first()
    dt_str = sess.session_datetime.strftime('%Y-%m-%d %H:%M')
    p.drawString(margin_x, y, f"Сеанс: {dt_str}")
    y -= 8 * mm

    for t in data['tickets']:
        p.drawString(
            margin_x,
            y,
            f"Місце: {t['seatNumber']}   Ряд: {t['row']}   Ціна: {t['cost']} грн"
        )
        y -= 6 * mm


    footer_y = 8 * mm
    p.setStrokeColorRGB(128, 0, 0)
    p.setLineWidth(0.5)
    p.line(margin_x, footer_y + 4 * mm, width - margin_x, footer_y + 4 * mm)

    p.setFont("DejaVuSans", 6)
    footer = (
        "Телефон: +38 (044) 123-45-67   •   "
        "Місто: Львів   •   "
        "Адреса: Червоної калини 81 "
    )
    p.drawString(margin_x + 4, footer_y, footer)

    p.showPage()
    p.save()
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name='ticket.pdf',
        mimetype='application/pdf'
    )

    
    
    
    



@app.route('/user', methods=['GET', 'POST'])
def user():
    global user_location
    global cities
    global user_device
    profile = session.get('user', "")
    if profile != "":
        return redirect(url_for('profile'))
    return render_template('User.html', city = "", cities = cities, profile = profile)


@app.route('/singup', methods=['GET', 'POST'])
def singup():
    global user_location
    global cities
    global user_device
    try:
        user_info = request.json
        print("User singed up:", user_info)
    except:
        print("No user info")
    for i in user_info:
        if user_info[i] == "":
            return jsonify({"success": False, "error": "Всі поля повинні бути заповнені!"}), 400
    existing_users = get_users()
    for i in existing_users:
        if i['email'] == user_info['email']:
            return jsonify({"success": False, "error": "Цей email вже зареєстрований!"}), 400
        if i['login'] == user_info['login']:
            return jsonify({"success": False, "error": "Цей логін вже зайнятий!"}), 400 
    try: 
        add_user(first_name=user_info['first_name'], last_name=user_info['last_name'], email=user_info['email'], login=user_info['login'], password=hashlib.sha256(user_info['password'].encode()).hexdigest(), bought_tickets_summary=0)
        db.session.commit()
        print("User added")       
        return jsonify({"success": True, "message": "Ви успішно зареєструвались!"}), 200
        # return render_template('User-cabinet.html', city = "", cities = cities)
    except Exception as e:
        print(e)
        return jsonify({"success": False, "error": "Щось пішло не так!"}), 400



@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.pop('user', None)
    return redirect(url_for('user'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    global user_location
    global cities
    global user_device
    try:
        user_info = request.json
        print("User logged in:", user_info)
    except:
        print("No user info")
    for i in user_info:
        if user_info[i] == "":
            return jsonify({"success": False, "error": "Всі поля повинні бути заповнені!"}), 400
    existing_users = get_users()
    print(existing_users)
    print("___________________________________________________________________________________")
    for i in existing_users:
        if i["login"] == user_info['login']:
            print (i["login"] == user_info['login'])
            print (i["password"])
            print (hashlib.sha256(user_info['password'].encode()).hexdigest())
            if i['password'] == hashlib.sha256(user_info['password'].encode()).hexdigest():
                flask_session['user'] = i['login']
                print(flask_session['user'])
                return jsonify({"success": True, "message": "Ви успішно увійшли!"}), 200
            
        
    return jsonify({"success": False, "error": "Невірний логін або пароль!"}), 400


@app.route('/user')
def button_click():
    global user_location
    global cities
    global user_device
    return render_template('User.html', city = "", cities = cities)

@app.route('/profile')
def profile():
    global user_location
    global cities
    global user_device
    user_ = User.query.filter_by(login=session['user']).first()
    films = []
    try: 
        history = Ticket.query.filter_by(user_id=user_.id).all()
        for i in history: 
            print(Film.query.filter_by(film_id=i.session.film_id).first().name)
            films.append(Film.query.filter_by(film_id=i.session.film_id).first().name)
        print(films)
    except Exception as e:
        print("No history")
        print(e)
    return render_template('User-cabinet.html', city = "", cities = cities, user=user_, films=films)



@app.route('/set_city', methods=['POST'])
def set_city():
    data = request.json
    session['city'] = data.get('city')
    return '', 204



@app.route('/market', methods=['POST', 'GET'])
def market():
    global user_location
    global cities
    global user_device
    return render_template('Market.html', city = "", cities = cities)








if __name__ == "__main__":
    with app.app_context():
        create_sample_data()
        db.create_all()
        
    app.run(debug=True)