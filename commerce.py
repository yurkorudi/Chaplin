"""Transactional booking, local demonstration payments and storefront."""
from datetime import datetime, timedelta
from decimal import Decimal
from functools import wraps
from io import BytesIO
from pathlib import Path
import hashlib
import hmac
import secrets
import uuid

from flask import abort, current_app, flash, g, jsonify, redirect, render_template, request, send_file, session as browser, url_for
from flask_wtf import CSRFProtect, FlaskForm
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash
from extensions import db
from models import Cinema, Hall, Film, Session, Seat, Ticket, User, Order, OrderItem, SeatReservation, Product, Category

def now():
    return datetime.now()

def user_required(role=None):
    if not g.user:
        abort(401, description='Увійдіть у свій обліковий запис.')
    if role and g.user.role not in role:
        abort(403)
    return g.user

def money(value):
    from decimal import InvalidOperation
    try:
        result=Decimal(str(value)).quantize(Decimal('.01'))
        if not result.is_finite() or abs(result)>Decimal('99999999'):
            raise ValueError('Некоректна грошова сума.')
        return result
    except InvalidOperation as error:
        raise ValueError('Некоректна грошова сума.') from error

def data():
    value = request.get_json(silent=True) if request.is_json else request.form
    if not value or not hasattr(value, 'get'):
        raise ValueError('Невірні дані запиту.')
    return value

def positive_int(value, maximum=1000000):
    if isinstance(value, bool):
        raise ValueError('Невірне число.')
    try:
        result = int(value)
    except (TypeError,ValueError) as error:
        raise ValueError('Невірне число.') from error
    if str(result) != str(value) or not 1 <= result <= maximum:
        raise ValueError('Невірне число.')
    return result

def owned_order(order_id, lock=False):
    user_required()
    query = Order.query.filter_by(id=order_id)
    order = (query.with_for_update() if lock else query).first_or_404()
    if order.user_id != g.user.id and g.user.role != 'admin':
        abort(403)
    return order

def occupied_positions(session_id):
    sold = [[t.row_index, t.column_index] for t in Ticket.query.filter_by(session_id=session_id)]
    held = [[r.row_index, r.column_index] for r in SeatReservation.query.filter_by(session_id=session_id).filter(SeatReservation.expires_at > now())]
    return sold + held

def validate_session(model):
    if not model.hall and model.hall_id:
        model.hall=db.session.get(Hall,model.hall_id)
    if not model.film and model.film_id:
        model.film=db.session.get(Film,model.film_id)
    if not model.cinema and model.cinema_id:
        model.cinema=db.session.get(Cinema,model.cinema_id)
    if not model.hall or model.hall.cinema_id != model.cinema_id:
        raise ValueError('Зал повинен належати вибраному кінотеатру.')
    if not model.film or model.film.duration <= 0 or model.session_duration != model.film.duration:
        raise ValueError('Тривалість сеансу має дорівнювати тривалості фільму.')
    if money(model.price) <= 0 or not Decimal('1') <= Decimal(model.vip_multiplier) <= Decimal('5'):
        raise ValueError('Вкажіть коректну ціну та коефіцієнт VIP.')
    # Serialize schedule changes for a hall, including empty schedules.
    db.session.query(Hall).filter_by(id=model.hall_id).with_for_update().one()
    buffer = timedelta(minutes=current_app.config['SESSION_BUFFER_MINUTES'])
    end = model.session_datetime + timedelta(minutes=model.session_duration) + buffer
    with db.session.no_autoflush:
        others = Session.query.filter(Session.hall_id == model.hall_id, Session.session_id != (model.session_id or 0)).all()
        for other in others:
            if model.session_datetime < other.session_datetime + timedelta(minutes=other.session_duration) + buffer and end > other.session_datetime:
                raise ValueError('Сеанс перетинається з іншим сеансом або часом підготовки залу.')

def reserve(session_id, selected, payment_method='online', staff=False):
    user_required(('admin', 'manager') if staff else None)
    sid = positive_int(session_id)
    show = Session.query.filter_by(session_id=sid).with_for_update().first_or_404()
    if show.session_datetime <= now() or not show.hall or show.hall.cinema_id != show.cinema_id:
        raise ValueError('Сеанс недоступний.')
    if staff:
        if g.user.role != 'admin' and g.user.cinema_id != show.cinema_id:
            abort(403)
    elif show.cinema.city != browser.get('city'):
        abort(403, description='Спочатку оберіть місто цього сеансу.')
    if not isinstance(selected, list) or not 1 <= len(selected) <= 12:
        raise ValueError('Оберіть від 1 до 12 місць.')
    SeatReservation.query.filter(SeatReservation.session_id == sid, SeatReservation.expires_at <= now()).delete(synchronize_session=False)
    occupied = {tuple(p) for p in occupied_positions(sid)}
    positions = set()
    order = Order(id=str(uuid.uuid4()), user_id=g.user.id, kind='tickets', total=0, payment_method=payment_method, expires_at=now()+timedelta(minutes=current_app.config['HOLD_MINUTES']))
    db.session.add(order)
    for item in selected:
        if not isinstance(item, dict):
            raise ValueError('Невірний формат місця.')
        row = item.get('row'); col = item.get('col', item.get('seatNumber'))
        if type(row) is not int or type(col) is not int:
            raise ValueError('Невірні координати місця.')
        structure = show.hall.structure
        if row < 0 or row >= len(structure) or col < 0 or col >= len(structure[row]) or structure[row][col] not in (1, 2):
            raise ValueError('Місце не існує у цьому залі.')
        if (row, col) in positions or (row, col) in occupied:
            abort(409, description='Місце вже зайняте або зарезервоване. Оновіть схему залу.')
        positions.add((row, col))
        price = money(show.price * (show.vip_multiplier if structure[row][col] == 2 else Decimal(1)))
        seat = Seat.query.filter_by(session_id=sid, row=row, column_index=col).first()
        if not seat:
            seat = Seat(session_id=sid, row=row, column_index=col, busy=False)
            db.session.add(seat); db.session.flush()
        order.total += price
        db.session.add(OrderItem(order=order, session_id=sid, seat_id=seat.seat_id, row_index=row, column_index=col, name=show.film.name, price=price, quantity=1))
        db.session.add(SeatReservation(session_id=sid, row_index=row, column_index=col, order_id=order.id, expires_at=order.expires_at))
    db.session.flush()
    return order

def complete_order(order):
    if order.status == 'paid':
        return
    if order.status != 'pending':
        abort(409, description='Замовлення більше не очікує оплату.')
    if order.expires_at and order.expires_at <= now():
        abort(409, description='Час резервування вичерпано. Створіть нове замовлення.')
    total = sum((item.price * item.quantity for item in order.items), Decimal(0))
    if money(total) != money(order.total) or order.currency != 'UAH':
        abort(409, description='Сума замовлення не пройшла перевірку.')
    if order.kind == 'tickets':
        for item in order.items:
            show = Session.query.filter_by(session_id=item.session_id).with_for_update().one()
            hold = SeatReservation.query.filter_by(order_id=order.id, session_id=item.session_id, row_index=item.row_index, column_index=item.column_index).first()
            if not hold or hold.expires_at <= now() or show.session_datetime <= now():
                abort(409, description='Резервування недійсне.')
            cell=show.hall.structure[item.row_index][item.column_index]
            expected=money(show.price*(show.vip_multiplier if cell==2 else Decimal(1)))
            if expected != money(item.price):
                abort(409,description='Ціна сеансу змінилася. Створіть нове бронювання.')
            db.session.add(Ticket(seat_id=item.seat_id, session_id=item.session_id, user_id=order.user_id, cost=item.price, row_index=item.row_index, column_index=item.column_index, cinema_id=str(show.cinema_id), sell_type=order.payment_method, order_id=order.id, token=secrets.token_urlsafe(32)))
            db.session.get(Seat,item.seat_id).busy=True
        # Keep a permanent reservation alongside the unique paid ticket.
        # Removing holds is safe because booking serializes on the session row.
        SeatReservation.query.filter_by(order_id=order.id).delete(synchronize_session=False)
    elif order.kind == 'shop':
        for item in sorted(order.items,key=lambda i:i.product_id):
            product=Product.query.filter_by(id=item.product_id).with_for_update().one()
            if money(product.price)!=money(item.price):
                abort(409,description='Ціна товару змінилася. Скасуйте та повторіть замовлення.')
    order.status = 'paid'; order.paid_at = now()
    db.session.flush()

def buy_ticket():
    import json
    d = data()
    selected = d.get('tickets') if request.is_json else json.loads(d.get('selected_seats', '[]'))
    order = reserve(d.get('session_id'), selected)
    db.session.commit()
    browser['last_order'] = order.id
    if request.is_json:
        return jsonify(order_id=order.id, total=str(order.total), redirect=url_for('payment', order_id=order.id)), 201
    return redirect(url_for('payment', order_id=order.id))

def payment(order_id):
    order = owned_order(order_id)
    from liqpay_payment import enabled
    return render_template('payment.html', order=order,liqpay_enabled=enabled())

def demo_pay(order_id):
    if not current_app.config['PAYMENT_DEMO_MODE'] or request.remote_addr not in ('127.0.0.1', '::1'):
        abort(403)
    order = owned_order(order_id, lock=True)
    if order.payment_method != 'online':
        abort(409)
    complete_order(order)
    order.is_demo = True
    db.session.commit()
    return redirect(url_for('payment', order_id=order.id))

def cancel_order(order_id):
    order = owned_order(order_id, lock=True)
    if order.status != 'pending':
        abort(409)
    if order.kind == 'shop':
        for item in sorted(order.items, key=lambda i: i.product_id):
            product = Product.query.filter_by(id=item.product_id).with_for_update().one()
            product.stock += item.quantity
    SeatReservation.query.filter_by(order_id=order.id).delete(synchronize_session=False)
    order.status = 'cancelled'
    db.session.commit()
    return redirect(url_for('profile'))

def ticket_confirmation():
    if not browser.get('last_order'):
        return redirect(url_for('profile'))
    return redirect(url_for('payment', order_id=browser['last_order']))

def ticket_pdf():
    from tickets_pdf import build_pdf
    order = owned_order(request.args.get('order_id') or browser.get('last_order'))
    if order.status != 'paid' or order.kind != 'tickets':
        abort(403)
    return send_file(build_pdf(order), mimetype='application/pdf', as_attachment=True, download_name=f'Chaplin-{order.id[:8]}.pdf')

def verify_ticket(token):
    user_required(('admin', 'manager'))
    ticket = Ticket.query.filter_by(token=token).first_or_404()
    if g.user.role != 'admin' and ticket.session.cinema_id != g.user.cinema_id:
        abort(403)
    return render_template('verify_ticket.html', ticket=ticket)

def login():
    if request.method == 'GET':
        return render_template('auth.html', register=False)
    d = data(); login_name = str(d.get('login', '')).strip()[:100]
    account = User.query.filter_by(login=login_name).first()
    password = str(d.get('password', ''))
    valid = False
    if account:
        if account.password.startswith(('scrypt:', 'pbkdf2:')):
            valid = check_password_hash(account.password, password)
        elif len(account.password) == 64:
            valid = hmac.compare_digest(account.password, hashlib.sha256(password.encode()).hexdigest())
            if valid:
                account.password = generate_password_hash(password)
                db.session.commit()
    if not valid:
        if request.is_json:
            return jsonify(error='Невірний логін або пароль.'), 400
        flash('Невірний логін або пароль.'); return render_template('auth.html', register=False), 400
    city = browser.get('city'); browser.clear()
    browser['user_id'] = account.id; browser['user'] = account.login; browser['city'] = city or 'Київ'
    if request.is_json:
        return jsonify(success=True)
    return redirect(url_for('profile'))

def singup():
    if request.method == 'GET':
        return render_template('auth.html', register=True)
    d = data()
    required = ('first_name', 'last_name', 'email', 'login', 'password')
    if any(not str(d.get(key, '')).strip() for key in required):
        raise ValueError('Заповніть усі поля.')
    if len(d['password']) < 10 or len(d['password']) > 200 or '@' not in d['email'] or len(d['email']) > 100:
        raise ValueError('Перевірте email; пароль повинен містити від 10 до 200 символів.')
    if any(len(d[k]) > limit for k, limit in [('first_name',50),('last_name',50),('login',100)]):
        raise ValueError('Занадто довге значення поля.')
    account = User(first_name=d['first_name'].strip(), last_name=d['last_name'].strip(), email=d['email'].strip().lower(), login=d['login'].strip(), password=generate_password_hash(d['password']), bought_tickets_summary=0, role='customer')
    db.session.add(account); db.session.commit()
    if request.is_json:
        return jsonify(success=True), 201
    flash('Обліковий запис створено. Увійдіть.'); return redirect(url_for('login'))

def logout():
    if request.method=='GET':
        return render_template('logout.html')
    browser.clear(); return redirect(url_for('homepage'))

def user():
    return redirect(url_for('profile') if g.user else url_for('login'))

def admin_login():
    return redirect(url_for('login'))

manager_login = admin_login
admin_logout = logout
manager_logout = logout

def profile():
    user_required()
    orders = Order.query.filter_by(user_id=g.user.id).order_by(Order.created_at.desc()).limit(100).all()
    legacy_tickets=Ticket.query.filter_by(user_id=g.user.id,order_id=None).order_by(Ticket.date_of_purchase.desc()).limit(100).all()
    return render_template('profile.html', orders=orders,legacy_tickets=legacy_tickets)

def update_profile():
    account = user_required(); d = data()
    for key, limit in [('first_name', 50), ('last_name', 50), ('email', 100), ('phone',25)]:
        value = str(d.get(key, '')).strip()
        if len(value) > limit or key != 'phone' and not value:
            raise ValueError('Перевірте поля профілю.')
        if key == 'email' and '@' not in value:
            raise ValueError('Невірний email.')
        setattr(account, key, value)
    if d.get('new_password'):
        if not check_password_hash(account.password, d.get('current_password', '')) or not 10 <= len(d['new_password']) <= 200:
            raise ValueError('Перевірте поточний пароль та довжину нового пароля (10–200 символів).')
        account.password = generate_password_hash(d['new_password'])
    db.session.commit(); flash('Профіль збережено.'); return redirect(url_for('profile'))

def set_city():
    city = data().get('city')
    if city not in g.cities:
        raise ValueError('Невідоме місто.')
    browser['city'] = city
    return '', 204

def schedule():
    shows = Session.query.join(Cinema).filter(Cinema.city == browser['city'], Session.session_datetime > now()).order_by(Session.session_datetime).limit(300).all()
    return render_template('schedule_live.html', shows=shows)

def available_sessions():
    d = data(); day = datetime.strptime(d.get('date', ''), '%Y-%m-%d')
    shows = Session.query.join(Cinema).filter(Cinema.city == browser['city'], Session.session_datetime >= day, Session.session_datetime < day+timedelta(days=1)).all()
    return jsonify([{'session_id':s.session_id,'film':s.film.name,'time':s.session_datetime.strftime('%H:%M'),'price':str(s.price)} for s in shows])

def book():
    return redirect(url_for('movie', movie_name=request.args.get('movie_name', '')))

def market():
    query = Product.query.filter_by(active=True)
    search = request.args.get('q', '').strip()[:100]
    category = request.args.get('category', type=int)
    if search:
        query = query.filter(Product.name.contains(search, autoescape=True))
    if category:
        query = query.filter_by(category_id=category)
    products = query.order_by(Product.id).paginate(page=request.args.get('page',1,type=int), per_page=20, error_out=False)
    return render_template('market_live.html', products=products, categories=Category.query.order_by(Category.name).all())

def product_detail(product_id):
    return render_template('product.html', product=Product.query.filter_by(id=product_id,active=True).first_or_404())

def cart_items():
    cart = browser.get('cart', {})
    products = Product.query.filter(Product.id.in_([int(k) for k in cart] or [0])).all()
    return [(p, int(cart[str(p.id)])) for p in products]

def cart():
    items = cart_items()
    return render_template('cart.html', items=items, total=sum((p.price*q for p,q in items),Decimal(0)), cinemas=Cinema.query.filter_by(city=browser['city']).all())

def cart_update():
    d = data(); pid = positive_int(d.get('product_id'))
    product = db.session.get(Product, pid)
    if not product or not product.active:
        abort(404)
    quantity = 0 if str(d.get('quantity'))=='0' else positive_int(d.get('quantity',1),20)
    if not 0 <= quantity <= min(product.stock, 20):
        raise ValueError('Перевірте кількість та наявність товару (максимум 20).')
    basket = dict(browser.get('cart', {}))
    if quantity:
        if len(basket) >= 50 and str(pid) not in basket:
            raise ValueError('Кошик переповнений.')
        basket[str(pid)] = quantity
    else:
        basket.pop(str(pid), None)
    browser['cart'] = basket
    return redirect(url_for('cart'))

def checkout():
    user_required(); d = data()
    fulfillment = d.get('fulfillment'); method = d.get('payment_method')
    if fulfillment not in ('pickup','nova_poshta') or method not in ('online','cinema') or fulfillment == 'nova_poshta' and method != 'online':
        raise ValueError('Доставка підтримує лише онлайн-оплату.')
    delivery = {k: str(d.get(k,'')).strip()[:200] for k in ('name','phone','city','branch','cinema_id')}
    if not delivery['name'] or not delivery['phone']:
        raise ValueError('Вкажіть одержувача та телефон.')
    if fulfillment == 'nova_poshta' and (not delivery['city'] or not delivery['branch']):
        raise ValueError('Вкажіть місто та відділення / поштомат Нової пошти.')
    if fulfillment == 'pickup':
        cinema = Cinema.query.filter_by(cinema_id=positive_int(delivery['cinema_id']), city=browser['city']).first()
        if not cinema:
            raise ValueError('Оберіть кінотеатр у поточному місті.')
        delivery['cinema'] = cinema.name
    basket = browser.get('cart', {})
    if not basket:
        raise ValueError('Кошик порожній.')
    order = Order(id=str(uuid.uuid4()),user_id=g.user.id,kind='shop',total=0,fulfillment=fulfillment,payment_method=method,delivery=delivery)
    db.session.add(order)
    for key in sorted(basket, key=int):
        product = Product.query.filter_by(id=int(key)).with_for_update().first()
        quantity = positive_int(basket[key],20)
        if not product or not product.active or product.stock < quantity:
            abort(409, description='Товару вже немає в достатній кількості.')
        product.stock -= quantity
        order.total += money(product.price)*quantity
        db.session.add(OrderItem(order=order,product_id=product.id,name=product.name,price=product.price,quantity=quantity))
    db.session.commit(); browser.pop('cart',None)
    return redirect(url_for('payment',order_id=order.id))

def moder():
    user_required(('admin','manager'))
    query = Session.query.filter(Session.session_datetime > now())
    if g.user.role == 'manager':
        query = query.filter_by(cinema_id=g.user.cinema_id)
    shows = query.order_by(Session.session_datetime).limit(200).all()
    selected = request.args.get('session_id',type=int)
    show = next((s for s in shows if s.session_id == selected),None)
    sold=[[t.row_index,t.column_index] for t in Ticket.query.filter_by(session_id=show.session_id)] if show else []
    return render_template('cashier.html',shows=shows,show=show,sold=sold,occupied=occupied_positions(show.session_id) if show else [])

admin_tickets = moder

def cashier_sale():
    import json
    d = data(); method = d.get('payment_method')
    if method not in ('cash','card'):
        raise ValueError('Оберіть готівку або картку.')
    if not current_app.config['PAYMENT_DEMO_MODE']:
        abort(503,description='Касові продажі потребують налаштування ПРРО та підтвердження платежу. Доступний локальний деморежим.')
    order = reserve(d.get('session_id'),json.loads(d.get('selected_seats','[]')),method,staff=True)
    complete_order(order); order.is_demo=True
    db.session.commit(); browser['last_order']=order.id
    return redirect(url_for('payment',order_id=order.id))

def cashier_verify():
    user_required(('admin','manager'))
    token=str(data().get('token','')).strip()
    if not 20<=len(token)<=64 or not all(c.isalnum() or c in '-_' for c in token):
        raise ValueError('Вкажіть ідентифікатор із QR-коду квитка.')
    return redirect(url_for('verify_ticket',token=token))

def cashier_shop():
    user_required(('admin','manager'))
    query=Order.query.filter_by(kind='shop',fulfillment='pickup')
    if g.user.role!='admin':
        query=query.filter(Order.delivery['cinema_id'].as_string()==str(g.user.cinema_id))
    orders=query.order_by(Order.created_at.desc()).limit(200).all()
    return render_template('cashier_shop.html',orders=orders)

def collect_shop(order_id):
    user_required(('admin','manager'))
    d=data();method=d.get('payment_method')
    if method not in ('cash','card'):
        raise ValueError('Оберіть готівку або картку.')
    order=Order.query.filter_by(id=order_id).with_for_update().first_or_404()
    if order.kind!='shop' or order.fulfillment!='pickup' or not order.delivery:
        abort(409)
    if g.user.role!='admin' and str(order.delivery.get('cinema_id'))!=str(g.user.cinema_id):
        abort(403)
    if order.fulfillment_status=='collected':
        return redirect(url_for('cashier_shop'))
    if order.status=='pending' and order.payment_method=='cinema':
        if not current_app.config['PAYMENT_DEMO_MODE']:
            abort(503,description='Потрібне підключення касової оплати та ПРРО.')
        order.payment_method=method;complete_order(order);order.is_demo=True
    if order.status!='paid':
        abort(409,description='Замовлення ще не оплачене.')
    order.fulfillment_status='collected';db.session.commit()
    flash('Замовлення видано. Демо-продаж не є фіскальним чеком.')
    return redirect(url_for('cashier_shop'))

def validate_structure(structure):
    if not isinstance(structure,list) or not 1 <= len(structure) <= 30 or not all(isinstance(row,list) and 1 <= len(row) <= 40 and all(type(c) is int and c in (0,1,2) for c in row) for row in structure):
        raise ValueError('Зал: 1–30 рядів, 1–40 місць, значення 0, 1 або 2.')
    return structure

def update_hall(hall_id):
    user_required(('admin',)); d=data()
    hall=Hall.query.filter_by(id=hall_id).with_for_update().first_or_404()
    if hall.sessions:
        abort(409,description='Геометрію залу із сеансами змінювати не можна. Створіть новий зал.')
    structure=validate_structure(d.get('structure'))
    hall.structure=structure; hall.rows=len(structure); hall.columns=max(map(len,structure))
    db.session.commit(); return jsonify(id=hall.id)

def save_hall_structure(hall_id):
    return update_hall(hall_id)

def create_hall():
    user_required(('admin',)); d=data()
    cinema=Cinema.query.get_or_404(positive_int(d.get('cinema_id')))
    rows=positive_int(d.get('rows'),30); columns=positive_int(d.get('columns'),40)
    structure=validate_structure(d.get('structure') or [[1]*columns for _ in range(rows)])
    hall=Hall(name=str(d.get('name','Новий зал'))[:100],cinema_id=cinema.cinema_id,rows=len(structure),columns=max(map(len,structure)),structure=structure)
    db.session.add(hall); db.session.commit(); return jsonify(id=hall.id),201

def install(app, admin, base_view):
    from collections import defaultdict, deque
    import time
    attempts=defaultdict(deque)
    from admin_forms import AdminForm
    base_view.form_base_class=AdminForm
    csrf=CSRFProtect(app)

    @app.before_request
    def prepare_request():
        if request.endpoint == 'static':
            return
        g.user=db.session.get(User,browser.get('user_id')) if browser.get('user_id') else None
        g.cities=[c for (c,) in db.session.query(Cinema.city).filter(Cinema.city.isnot(None)).distinct().order_by(Cinema.city)]
        if browser.get('city') not in g.cities:
            browser['city']='Київ' if 'Київ' in g.cities else (g.cities[0] if g.cities else '')
        if request.path.startswith('/admin'):
            if request.path not in ('/admin/login','/admin/logout'):
                user_required(('admin',))
        # Compatibility flags are derived from the database role on every request.
        browser['is_admin']=bool(g.user and g.user.role=='admin')
        browser['is_manager']=bool(g.user and g.user.role in ('admin','manager'))
        if request.path in ('/login','/singup') and request.method=='POST':
            bucket=attempts[request.remote_addr]; timestamp=time.monotonic()
            while bucket and bucket[0]<timestamp-60:
                bucket.popleft()
            if len(bucket)>=30:
                abort(429,description='Забагато спроб. Спробуйте за хвилину.')
            bucket.append(timestamp)

    @app.context_processor
    def context():
        return dict(cities=getattr(g,'cities',[]),current_user=getattr(g,'user',None),selected_city=browser.get('city',''),profile=browser.get('user',''),demo_mode=app.config['PAYMENT_DEMO_MODE'])

    @app.after_request
    def headers(response):
        response.headers['X-Content-Type-Options']='nosniff'
        response.headers['X-Frame-Options']='SAMEORIGIN'
        response.headers['Referrer-Policy']='same-origin'
        if request.endpoint != 'static':
            response.headers['Cache-Control']='no-store'
        return response

    @app.teardown_request
    def rollback(error):
        if error:
            db.session.rollback()

    @app.errorhandler(ValueError)
    def invalid(error):
        db.session.rollback()
        if request.is_json:
            return jsonify(error=str(error)),400
        return render_template('error.html',message=str(error)),400

    @app.errorhandler(IntegrityError)
    def duplicate(error):
        db.session.rollback(); app.logger.warning('Constraint violation: %s',error.orig.__class__.__name__)
        if request.is_json:
            return jsonify(error='Запис уже існує або дані змінилися. Оновіть сторінку й повторіть дію.'),409
        return render_template('error.html',message='Запис уже існує або дані змінилися. Оновіть сторінку й повторіть дію.'),409

    for code in (400,401,403,404,409,429,503):
        def handle(error):
            db.session.rollback()
            if request.is_json:
                return jsonify(error=error.description),error.code
            return render_template('error.html',message=error.description),error.code
        app.register_error_handler(code,handle)

    app.add_url_rule('/payment/<order_id>','payment',payment)
    app.add_url_rule('/payment/<order_id>/demo','demo_pay',demo_pay,methods=['POST'])
    app.add_url_rule('/orders/<order_id>/cancel','cancel_order',cancel_order,methods=['POST'])
    app.add_url_rule('/tickets/verify/<token>','verify_ticket',verify_ticket)
    app.add_url_rule('/profile/update','update_profile',update_profile,methods=['POST'])
    app.add_url_rule('/cart','cart',cart)
    app.add_url_rule('/cart/update','cart_update',cart_update,methods=['POST'])
    app.add_url_rule('/checkout','checkout',checkout,methods=['POST'])
    app.add_url_rule('/market/<int:product_id>','product_detail',product_detail)
    app.add_url_rule('/manager/','cashier',moder)
    app.add_url_rule('/manager/sale','cashier_sale',cashier_sale,methods=['POST'])
    app.add_url_rule('/manager/verify','cashier_verify',cashier_verify,methods=['POST'])
    app.add_url_rule('/manager/shop','cashier_shop',cashier_shop)
    app.add_url_rule('/manager/shop/<order_id>/collect','collect_shop',collect_shop,methods=['POST'])
    app.add_url_rule('/get_city','get_city',lambda:jsonify(city=browser.get('city')))
    def health():
        from sqlalchemy import text
        db.session.execute(text('SELECT 1'))
        return jsonify(application='chaplin',database='ok')
    app.add_url_rule('/healthz','health',health)
    from liqpay_payment import checkout as liqpay_checkout,callback
    app.add_url_rule('/payment/<order_id>/liqpay','liqpay_checkout',liqpay_checkout,methods=['POST'])
    # Webhooks authenticate with the provider signature, not a browser cookie.
    app.add_url_rule('/payments/liqpay/callback','liqpay_callback',csrf.exempt(callback),methods=['POST'])
    from admin_support import install_admin
    install_admin(app,admin,base_view)
