"""Preserve Flask-Admin management while securing every entity and schedule edit."""
from datetime import datetime, timedelta
from decimal import Decimal
from flask import g, render_template, request, redirect, url_for, flash, abort
from flask_wtf import FlaskForm
from sqlalchemy import event, inspect
from sqlalchemy.orm import Session as ORMSession
from werkzeug.security import generate_password_hash
from flask_admin.actions import action
from flask_admin.form import ImageUploadField
from wtforms import PasswordField
from extensions import db
from models import *
from admin_forms import AdminForm

def install_admin(app,admin,base):
    class UserView(base):
        form_args={'cinema':{'query_factory':lambda:Cinema.query.order_by(Cinema.name).all(),'get_label':'name','allow_blank':True}}
        form_columns=['first_name','last_name','email','login','phone','role','cinema','new_password']
        column_list=['login','first_name','last_name','email','role','cinema']
        column_searchable_list=['login','email','first_name','last_name']
        column_filters=['role']
        form_extra_fields={'new_password':PasswordField('Новий пароль (мінімум 10 символів)')}
        can_delete=False
        def on_model_change(self,form,model,is_created):
            password=form.new_password.data
            if is_created and not password or password and not 10<=len(password)<=200:
                raise ValueError('Пароль повинен містити від 10 до 200 символів.')
            if password:
                model.password=generate_password_hash(password)
            if model.role not in ('customer','admin','manager'):
                raise ValueError('Невідома роль.')
            if model.role=='manager' and not model.cinema:
                raise ValueError('Менеджеру потрібно призначити кінотеатр.')
            if model.bought_tickets_summary is None:
                model.bought_tickets_summary=0
    class ProductView(base):
        form_args={'category':{'query_factory':lambda:Category.query.order_by(Category.name).all(),'get_label':'name'}}
        form_columns=['name','description','category','price','stock','image','active']
        column_list=['name','category','price','stock','active']
        column_searchable_list=['name','description']
        column_filters=['active','category.name']
        can_delete=False
    class CategoryView(base):
        form_columns=['name'];column_searchable_list=['name']
        can_delete=False
    class TicketView(base):
        can_create=False;can_edit=False;can_delete=False
        column_list=['ticket_id','session','user','row_index','column_index','cost','sell_type','date_of_purchase']
        column_filters=['session_id','user_id','sell_type']
        column_searchable_list=['token']
    class SeatView(base):
        can_create=False;can_edit=False;can_delete=False
        column_list=['seat_id','session','row','column_index','busy']
        column_filters=['session_id']
    class OrderView(base):
        can_create=False;can_edit=False;can_delete=False
        can_view_details=True
        column_details_list=['id','user_id','kind','status','total','currency','payment_method','fulfillment','fulfillment_status','delivery','items','created_at','paid_at','is_demo','fiscal_status']
        column_list=['id','user_id','kind','status','total','payment_method','fulfillment','fulfillment_status','created_at','is_demo','fiscal_status']
        column_searchable_list=['id']
        column_filters=['kind','status','payment_method','user_id']
        @action('ready','Позначити готовими до видачі','Позначити вибрані замовлення самовивозу готовими?')
        def ready(self,ids):
            for order_id in sorted(ids):
                order=Order.query.filter_by(id=order_id).with_for_update().first()
                if order and order.kind=='shop' and order.fulfillment=='pickup' and order.status in ('pending','paid') and order.fulfillment_status=='pending':
                    order.fulfillment_status='ready'
            db.session.commit();flash('Замовлення оновлено. Статус оплати не змінено.')
        @action('shipped','Позначити відправленими','Підтверджуєте фактичне відправлення сплачених замовлень?')
        def shipped(self,ids):
            for order_id in sorted(ids):
                order=Order.query.filter_by(id=order_id).with_for_update().first()
                if order and order.kind=='shop' and order.fulfillment=='nova_poshta' and order.status=='paid':
                    order.fulfillment_status='shipped'
            db.session.commit();flash('Сплачені замовлення доставки позначено відправленими.')
        @action('cancel_pending','Скасувати неоплачені замовлення','Скасувати вибрані неоплачені замовлення та повернути залишки?')
        def cancel_pending(self,ids):
            for order_id in sorted(ids):
                order=Order.query.filter_by(id=order_id).with_for_update().first()
                if not order or order.status!='pending':
                    continue
                if order.kind=='shop':
                    for item in sorted(order.items,key=lambda i:i.product_id):
                        product=Product.query.filter_by(id=item.product_id).with_for_update().one()
                        product.stock+=item.quantity
                SeatReservation.query.filter_by(order_id=order.id).delete(synchronize_session=False)
                order.status='cancelled'
            db.session.commit();flash('Неоплачені замовлення скасовано.')
    admin.add_view(UserView(User,db.session,name='Користувачі'))
    admin.add_view(TicketView(Ticket,db.session,name='Квитки'))
    admin.add_view(SeatView(Seat,db.session,name='Місця'))
    admin.add_view(OrderView(Order,db.session,name='Замовлення'))
    admin.add_view(ProductView(Product,db.session,name='Товари'))
    admin.add_view(CategoryView(Category,db.session,name='Категорії'))
    class ReceiptView(base):
        can_create=False;can_edit=False;can_delete=False
        column_list=['order_id','provider_reference','amount','currency','status','received_at']
        column_filters=['status'];column_searchable_list=['order_id','provider_reference']
    admin.add_view(ReceiptView(PaymentReceipt,db.session,name='Підтвердження платежів'))
    for view in admin._views:
        if hasattr(view,'form_base_class'):
            view.form_base_class=AdminForm
        if getattr(view,'model',None)==Session:
            view.can_delete=False
            view.column_filters=['cinema.city','cinema.name','hall.name']
            view.column_searchable_list=['film.name']
        if getattr(view,'model',None)==Film:
            view.can_delete=False;view.column_searchable_list=['name','genre']
        if getattr(view,'model',None) in (Hall,Cinema):
            view.can_delete=False

    def before_flush(orm,flush_context,instances):
        from commerce import validate_session,validate_structure
        with orm.no_autoflush:
            for model in list(orm.new)+list(orm.dirty):
                if isinstance(model,Session):
                    state=inspect(model)
                    # Forms may assign relationships before the FK synchronizes.
                    if model.hall:
                        model.hall_id=model.hall.id
                    if model.cinema:
                        model.cinema_id=model.cinema.cinema_id
                    if model.film:
                        model.film_id=model.film.film_id
                    if model.session_id and model in orm.dirty:
                        changed=any(state.attrs[key].history.has_changes() for key in ['film_id','cinema_id','hall_id','session_datetime','session_duration','price','vip_multiplier'])
                        if changed and (Ticket.query.filter_by(session_id=model.session_id).first() or SeatReservation.query.filter_by(session_id=model.session_id).filter(SeatReservation.expires_at>datetime.now()).first()):
                            raise ValueError('Сеанс із квитками або активними резервами змінювати не можна.')
                    validate_session(model)
                if isinstance(model,Hall):
                    validate_structure(model.structure)
                    model.rows=len(model.structure);model.columns=max(map(len,model.structure))
                    state=inspect(model)
                    if model.id and model in orm.dirty and any(state.attrs[k].history.has_changes() for k in ['name','structure','rows','columns','cinema_id','cinema']):
                        if Session.query.filter_by(hall_id=model.id).first():
                            raise ValueError('Зал із сеансами змінювати не можна. Створіть інший зал.')
                if isinstance(model,Film) and model in orm.dirty:
                    state=inspect(model)
                    if state.attrs.duration.history.has_changes() and Session.query.filter_by(film_id=model.film_id).first():
                        raise ValueError('Тривалість фільму із сеансами змінювати не можна.')
                    if state.attrs.name.history.has_changes() and Ticket.query.join(Session).filter(Session.film_id==model.film_id).first():
                        raise ValueError('Назву фільму з проданими квитками змінювати не можна.')
                if isinstance(model,Product):
                    if model.price is None or Decimal(model.price)<0 or model.stock is None or model.stock<0:
                        raise ValueError('Ціна та залишок не можуть бути від’ємними.')
                    if model.image and not model.image.startswith('/static/'):
                        raise ValueError('Використовуйте зображення з /static/.')
    event.listen(ORMSession,'before_flush',before_flush)

    @app.route('/admin/schedule/new',methods=['GET','POST'])
    def new_session():
        from commerce import user_required,positive_int,money
        user_required(('admin',))
        if request.method=='POST':
            hall=Hall.query.get_or_404(positive_int(request.form.get('hall_id')))
            cinema=Cinema.query.get_or_404(positive_int(request.form.get('cinema_id')))
            film=Film.query.get_or_404(positive_int(request.form.get('film_id')))
            if hall.cinema_id!=cinema.cinema_id or cinema.city!=request.form.get('city'):
                raise ValueError('Місто, кінотеатр та зал не відповідають одне одному.')
            price=money(request.form.get('price'))
            show=Session(film=film,cinema=cinema,hall=hall,film_id=film.film_id,cinema_id=cinema.cinema_id,hall_id=hall.id,session_datetime=datetime.fromisoformat(request.form.get('start')),session_duration=film.duration,price=price,vip_multiplier=Decimal('1.5'))
            db.session.add(show);db.session.commit();flash('Сеанс створено.')
            return redirect('/admin/session/')
        return render_template('admin/new_session.html',cinemas=Cinema.query.order_by(Cinema.city).all(),halls=Hall.query.all(),films=Film.query.order_by(Film.name).all())
