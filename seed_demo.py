"""Idempotent local demo records, dated relative to the current day."""
from datetime import datetime, timedelta, time
from decimal import Decimal
from pathlib import Path
import secrets
from werkzeug.security import generate_password_hash
from extensions import db
from models import *

def seed(write_credentials=True):
    credentials=[]
    today=datetime.now().date()
    cinemas=[]
    for city,address in [('Київ','вул. Хрещатик, 1 (демо)'),('Львів','просп. Свободи, 10 (демо)')]:
        cinema=Cinema.query.filter_by(name=f'Chaplin {city}',city=city).first()
        if not cinema:
            cinema=Cinema(name=f'Chaplin {city}',city=city,location=address,work_schedule='09:00–23:00')
            db.session.add(cinema); db.session.flush()
        cinemas.append(cinema)
        for number in (1,2):
            hall=Hall.query.filter_by(cinema_id=cinema.cinema_id,name=f'Зал {number}').first()
            if not hall:
                structure=[[1]*10 for _ in range(5)]+[[2]*10]
                db.session.add(Hall(cinema_id=cinema.cinema_id,name=f'Зал {number}',rows=6,columns=10,structure=structure))
    for login,role in [('demo','customer'),('admin','admin'),('manager','manager')]:
        if not User.query.filter_by(login=login).first():
            password=secrets.token_urlsafe(12)
            db.session.add(User(login=login,email=f'{login}@chaplin.local',first_name={'demo':'Гість','admin':'Адміністратор','manager':'Касир'}[login],last_name='Демо',password=generate_password_hash(password),bought_tickets_summary=0,role=role,cinema_id=cinemas[0].cinema_id if role=='manager' else None))
            credentials.append(f'{role}: {login} / {password}')
    films=[]
    for name,genre,duration,poster,age in [('Дикий робот','Анімація',102,'robotposter.jpg','0+'),('Веном: Останній танець','Фантастика',109,'venomposter.jpg','16+'),('Гладіатор II','Пригоди',148,'gladiatorposter.jpg','16+'),('Червоний','Комедія',123,'redposter.jpg','12+'),('Буча','Драма',118,'buchaposter.jpg','16+'),('Wicked: Чародійка','Фентезі',160,'wickedposter.jpg','6+')]:
        film=Film.query.filter_by(name=name).first()
        if not film:
            path=f'/static/img/{poster}'
            image=Image.query.filter_by(path=path).first()
            if not image:
                image=Image(type='Poster',path=path);db.session.add(image);db.session.flush()
            film=Film(name=name,genre=genre,description=f'{name} — демонстраційний показ у мережі Chaplin Cinema.',duration=duration,age=age,image_id=image.image_id,release_start_date=today,release_end_date=today+timedelta(days=60),director='Демонстраційний розклад')
            db.session.add(film);db.session.flush()
        films.append(film)
    db.session.flush()
    for city_index,cinema in enumerate(cinemas):
        for hall_index,hall in enumerate(Hall.query.filter_by(cinema_id=cinema.cinema_id).order_by(Hall.id)):
            for day in range(8):
                for index,hour in enumerate((10,14,18,21)):
                    start=datetime.combine(today+timedelta(days=day),time(hour,city_index*20))
                    if Session.query.filter_by(hall_id=hall.id,session_datetime=start).first():
                        continue
                    film=films[(day+index+hall_index+city_index)%len(films)]
                    conflict=False
                    for existing in Session.query.filter_by(hall_id=hall.id):
                        if start<existing.session_datetime+timedelta(minutes=existing.session_duration+15) and start+timedelta(minutes=film.duration+15)>existing.session_datetime:
                            conflict=True;break
                    if conflict:
                        continue
                    db.session.add(Session(film_id=film.film_id,cinema_id=cinema.cinema_id,hall_id=hall.id,session_datetime=start,session_duration=film.duration,price=Decimal(140+index*20+hall_index*10),vip_multiplier=Decimal('1.5')))
    categories=['Плюшеві іграшки','Фігурки','Брелоки','Чашки','Набори та подарунки']
    names=['Робот Боб — м’яка іграшка','Лисеня — плюшевий друг','Космічний кіт','Дракончик Піксель','Робот — колекційна фігурка','Космонавт Міні','Лицар кіноекрана','Чарівниця — фігурка','Брелок Chaplin Hat','Брелок Кінохлопавка','Брелок Зірка','Брелок Малий робот','Чашка Chaplin Cinema','Чашка Космічні пригоди','Чашка Кіновечір','Дитяча пляшка Зірочки','Набір Сімейний кіновечір','Подарунковий бокс Chaplin','Набір юного режисера','Рюкзак Кінопригоди']
    for index,name in enumerate(names):
        cat_name=categories[index//4]
        category=Category.query.filter_by(name=cat_name).first()
        if not category:
            category=Category(name=cat_name);db.session.add(category);db.session.flush()
        if not Product.query.filter_by(name=name).first():
            db.session.add(Product(name=name,category_id=category.id,description=f'{name}. Тематичний сувенір для шанувальників кіно. Наявність наведена лише для локальної демонстрації.',price=Decimal(149+index*25),stock=10+index,image='/static/img/merch.svg'))
    db.session.commit()
    if credentials and write_credentials:
        path=Path('.local/demo-accounts.txt');path.parent.mkdir(exist_ok=True)
        with path.open('a',encoding='utf-8') as stream:
            stream.write('Лише локальні демонстраційні облікові записи\n'+'\n'.join(credentials)+'\n')
    # A few genuinely paid demo tickets, through the same reservation/payment service.
    from commerce import reserve,complete_order
    from flask import g, session
    from app import app
    with app.test_request_context('/'):
        g.user=User.query.filter_by(login='demo').one();session['city']='Київ'
        shows=Session.query.join(Cinema).filter(Cinema.city=='Київ',Session.session_datetime>datetime.now()).order_by(Session.session_datetime,Session.session_id).limit(3).all()
        for show in shows:
            if Ticket.query.filter_by(session_id=show.session_id,row_index=0,column_index=0).first():
                continue
            order=reserve(show.session_id,[{'row':0,'col':0},{'row':0,'col':1}])
            complete_order(order);order.is_demo=True
            db.session.commit()

if __name__=='__main__':
    from app import app
    with app.app_context():
        seed()
