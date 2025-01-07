from flask import *
from user_agents import *
from flask_sqlalchemy import SQLAlchemy
from time import *


from extensions import db
from models import Image, User, Cinema, Session, Film, Seat, Ticket
from funcs import *
from modls import *


app = Flask(__name__)


app.config["SQLALCHEMY_DATABASE_URI"] = "mysql://zulu:zuludf345@64.225.100.209:3306/chaplin"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)



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


        add_user(phone_number="1234567890", first_name="John", last_name="Doe",
                email="john.doe@example.com", login="johndoe", password="password123", bought_tickets_summary=3)
        add_user(phone_number="0987654321", first_name="Jane", last_name="Smith",
                email="jane.smith@example.com", login="janesmith", password="password456", bought_tickets_summary=5)
        add_user(phone_number="1122334455", first_name="Alice", last_name="Brown",
                email="alice.brown@example.com", login="alicebrown", password="password789", bought_tickets_summary=1)
        add_user(phone_number="5566778899", first_name="Bob", last_name="Johnson",
                email="bob.johnson@example.com", login="bobjohnson", password="password101", bought_tickets_summary=2)


        add_session(film_id=1, cinema_id=1, session_datetime=datetime(2023, 5, 10, 18, 0), session_duration=120)
        add_session(film_id=2, cinema_id=2, session_datetime=datetime(2023, 6, 15, 20, 0), session_duration=110)
        add_session(film_id=3, cinema_id=3, session_datetime=datetime(2023, 7, 20, 19, 0), session_duration=100)
        add_session(film_id=4, cinema_id=4, session_datetime=datetime(2023, 8, 25, 21, 0), session_duration=130)


        add_seat(session_id=1, row=1, busy=False)
        add_seat(session_id=1, row=2, busy=True)
        add_seat(session_id=2, row=1, busy=False)
        add_seat(session_id=2, row=2, busy=True)


        add_ticket(user_phone_number="1234567890", seat_id=1, session_id=1)
        add_ticket(user_phone_number="0987654321", seat_id=2, session_id=1)
        add_ticket(user_phone_number="1122334455", seat_id=3, session_id=2)
        add_ticket(user_phone_number="5566778899", seat_id=4, session_id=2)
    print("created!")

# create_sample_data()


with app.app_context():
    print(get_seats())


cities = {
    "lviv":"Львів",
    "mor":"Моршин",
    "dol":"Долина",
    "oks":"Оксана",
}
user_location = []
user_device = 'None'




@app.route('/')
def early_start ():
    global user_device
    user_agent = parse(request.headers.get('User-Agent'))
    if user_agent.is_mobile:
        user_device = "android"
    else:
        user_device = "desktop"

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



@app.route('/home')
def homepage():
    global user_location
    global cities
    global user_device


    return render_template('Homepage.html', city = "", cities = cities)



@app.route('/movies')
def movies():
    global user_location
    global user_device
    if user_location == []:
        a = location()
    if user_device == 'desktop':
        print ('desktop version')
        return render_template('Movies.html', city = "", cities = cities)
    else: 
        print ('mobile version')
        return render_template('Movies.html', city = "", cities = cities)
    


@app.route('/movie')
def movie():
    global user_location
    global user_device
    global json
    film_name = request.args.get('movie_name')
    with app.app_context():
        film = Film_obj(film_name)


    if user_location == []:
        a = location()

    return render_template('Movie.html', city = "", cities = cities, movie_info = film.data)
        


@app.route('/about')
def about():
    global user_location
    global cities
    global user_device
    return render_template('About.html', city = "", cities = cities)


@app.route('/book', methods=['GET', 'POST'])
def book():
    global user_location
    global user_device
    global json

    if request.method == 'POST':
        film_name = request.args.get('movie_name')
        try:
            data = request.form.get("selectedSeats")
            seat_details = json.loads(data)

            for seat in seat_details:
                seat_number = seat.get("seatNumber")
                row = seat.get("row")
                cost = seat.get("cost")
                print(f"Seat ____!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! {seat_number} in row {row} costs {cost}.")
        except:
            pass
        with app.app_context():
            film = Film_obj(film_name)

        if user_location == []:
            a = location()


    if request.method == 'GET':
        try:
            selected_date = request.args.get('date')
            selected_hour = request.args.get('hour')
            film_name = request.args.get('film')
        except:
            pass
        print('___________________________________________________________________________________', film_name)
        with app.app_context():
            film = Film_obj(film_name)
        print (selected_date, selected_hour)
        return render_template('Booking.html', city = "", cities = cities, movie_info = film.data, date=selected_date, time=selected_hour)


    return render_template('Booking.html', city = "", cities = cities, movie_info = film.data)


@app.route('/ticket', methods=['POST'])
def ticket():
    content_type = request.headers.get('Content-Type')
    print("______________________________________________________", content_type)
    data = request.get_json()
    print(data)




@app.route('/user')
def user():
    global user_location
    global cities
    global user_device
    return render_template('User.html', city = "", cities = cities)

@app.route('/user')
def button_click():
    global user_location
    global cities
    global user_device
    return render_template('User.html', city = "", cities = cities)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='192.168.43.61')



