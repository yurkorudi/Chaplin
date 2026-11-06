"""Integration tests run on a freshly created disposable MySQL database."""
import re
import json
from datetime import datetime,timedelta
from decimal import Decimal
from concurrent.futures import ThreadPoolExecutor
from extensions import db
from models import *

def csrf(client,path='/login'):
    response=client.get(path)
    match=re.search(rb'name="csrf-token" content="([^"]+)"',response.data)
    assert match,response.data[:300]
    return match.group(1).decode()

def sign_in(client,login='demo'):
    return client.post('/login',data={'login':login,'password':'TestPassword123!','csrf_token':csrf(client)})

def post(client,url,payload):
    return client.post(url,json=payload,headers={'X-CSRFToken':csrf(client)})

def show_id(app,city='Київ'):
    with app.app_context():
        return Session.query.join(Cinema).filter(Cinema.city==city,Session.session_datetime>datetime.now()+timedelta(days=1)).order_by(Session.session_id).first().session_id

def test_public_pages_and_roles(app):
    c=app.test_client()
    for path in ['/home','/movies','/movie?movie_name=Дикий робот','/schedule','/market','/cart','/about','/login','/singup']:
        assert c.get(path).status_code==200,path
    for path in ['/admin/','/admin/film/','/admin/holls/','/profile','/manager/']:
        assert c.get(path).status_code==401,path
    assert sign_in(c).status_code==302
    assert c.get('/admin/film/').status_code==403
    assert c.get('/manager/').status_code==403

def test_filtered_pages_and_direct_session_link(app):
    c=app.test_client();sid=show_id(app)
    with app.app_context():
        show=db.session.get(Session,sid)
        film=show.film.name;cinema=show.cinema_id
        category=Category.query.first().id
    from urllib.parse import urlencode
    for path in ['/movie?'+urlencode({'movie_name':film,'session_id':sid}),'/market?category='+str(category),'/schedule?cinema='+str(cinema)]:
        assert c.get(path).status_code==200,path

def test_csrf_registration_profile(app):
    c=app.test_client()
    assert c.post('/login',json={'login':'demo','password':'x'}).status_code==400
    payload={'first_name':'Тест','last_name':'Гість','email':'new@example.local','login':'new','password':'TestPassword123!','role':'admin'}
    assert post(c,'/singup',payload).status_code==201
    assert sign_in(c,'new').status_code==302
    assert c.get('/admin/').status_code==403
    with app.app_context():
        account=User.query.filter_by(login='new').one()
        assert account.password.startswith('scrypt:') and account.role=='customer'
    assert c.post('/profile/update',data={'first_name':'Нове','last_name':'Ім’я','email':'new@example.local','phone':'0500000000','csrf_token':csrf(c)}).status_code==302

def test_booking_price_payment_pdf_owner(app):
    c=app.test_client();sign_in(c);sid=show_id(app)
    result=post(c,'/buy_ticket',{'session_id':sid,'tickets':[{'row':5,'col':8,'price':1,'cost':-99}]})
    assert result.status_code==201,result.data
    oid=result.json['order_id']
    with app.app_context():
        show=db.session.get(Session,sid);order=db.session.get(Order,oid)
        assert order.total==(show.price*show.vip_multiplier).quantize(Decimal('.01'))
        assert not order.tickets
    assert c.get('/ticket_pdf?order_id='+oid).status_code==403
    assert post(c,'/buy_ticket',{'session_id':sid,'tickets':[{'row':5,'col':8}]}).status_code==409
    for _ in range(2):
        assert c.post('/payment/'+oid+'/demo',data={'csrf_token':csrf(c)}).status_code==302
    with app.app_context():
        assert Ticket.query.filter_by(order_id=oid).count()==1
    pdf=c.get('/ticket_pdf?order_id='+oid)
    assert pdf.status_code==200 and pdf.data.startswith(b'%PDF') and len(pdf.data)>10000
    other=app.test_client();sign_in(other,'outsider')
    assert other.get('/payment/'+oid).status_code==403
    assert other.get('/ticket_pdf?order_id='+oid).status_code==403
    assert other.post('/payment/'+oid+'/demo',data={'csrf_token':csrf(other)}).status_code==403

def test_invalid_seats_and_city(app):
    c=app.test_client();sign_in(c);sid=show_id(app)
    for selection in [[{'row':-1,'col':0}],[{'row':0,'col':1000}],[{'row':True,'col':0}]]:
        assert post(c,'/buy_ticket',{'session_id':sid,'tickets':selection}).status_code==400
    assert post(c,'/buy_ticket',{'session_id':show_id(app,'Львів'),'tickets':[{'row':1,'col':2}]}).status_code==403
    assert post(c,'/set_city',{'city':'Львів'}).status_code==204
    assert 'Chaplin Львів'.encode() in c.get('/schedule').data
    assert post(c,'/buy_ticket',{'session_id':show_id(app,'Львів'),'tickets':[{'row':1,'col':2}]}).status_code==201

def test_expired_hold(app):
    c=app.test_client();sign_in(c);sid=show_id(app)
    result=post(c,'/buy_ticket',{'session_id':sid,'tickets':[{'row':4,'col':7}]});oid=result.json['order_id']
    with app.app_context():
        db.session.get(Order,oid).expires_at=datetime.now()-timedelta(minutes=1)
        SeatReservation.query.filter_by(order_id=oid).update({'expires_at':datetime.now()-timedelta(minutes=1)})
        db.session.commit()
    assert c.post('/payment/'+oid+'/demo',data={'csrf_token':csrf(c)}).status_code==409
    assert post(c,'/buy_ticket',{'session_id':sid,'tickets':[{'row':4,'col':7}]}).status_code==201

def test_payment_demo_gate(app):
    c=app.test_client();sign_in(c);sid=show_id(app)
    result=post(c,'/buy_ticket',{'session_id':sid,'tickets':[{'row':4,'col':6}]});oid=result.json['order_id']
    app.config['PAYMENT_DEMO_MODE']=False
    try:
        assert c.post('/payment/'+oid+'/demo',data={'csrf_token':csrf(c)}).status_code==403
    finally:
        app.config['PAYMENT_DEMO_MODE']=True
    assert c.post('/payment/'+oid+'/demo',data={'csrf_token':csrf(c)},environ_overrides={'REMOTE_ADDR':'192.0.2.1'}).status_code==403

def test_concurrent_same_seat(app):
    sid=show_id(app)
    def attempt(login):
        c=app.test_client();sign_in(c,login)
        return post(c,'/buy_ticket',{'session_id':sid,'tickets':[{'row':3,'col':9}]}).status_code
    with ThreadPoolExecutor(max_workers=2) as pool:
        statuses=list(pool.map(attempt,['demo','outsider']))
    assert sorted(statuses)==[201,409]

def test_shop_price_stock_shipping_cancel(app):
    c=app.test_client();sign_in(c)
    with app.app_context():
        p=Product.query.first();pid=p.id;price=p.price;stock=p.stock
    assert c.post('/cart/update',data={'product_id':pid,'quantity':2,'csrf_token':csrf(c)}).status_code==302
    payload={'fulfillment':'nova_poshta','payment_method':'cinema','name':'Гість','phone':'0500000000','city':'Львів','branch':'Відділення 1','total':'1'}
    assert post(c,'/checkout',payload).status_code==400
    payload['payment_method']='online';result=post(c,'/checkout',payload)
    assert result.status_code==302,result.data
    oid=result.location.rsplit('/',1)[-1]
    with app.app_context():
        assert db.session.get(Order,oid).total==price*2
        assert db.session.get(Product,pid).stock==stock-2
    assert c.get('/payment/'+oid).status_code==200
    assert c.post('/orders/'+oid+'/cancel',data={'csrf_token':csrf(c)}).status_code==302
    with app.app_context():
        assert db.session.get(Product,pid).stock==stock
    assert c.post('/orders/'+oid+'/cancel',data={'csrf_token':csrf(c)}).status_code==409

def test_admin_pages_conflicting_schedule(app):
    c=app.test_client();sign_in(c,'admin')
    for path in ['/admin/','/admin/film/','/admin/session/','/admin/hall/','/admin/cinema/','/admin/user/','/admin/ticket/','/admin/product/','/admin/category/','/admin/order/','/admin/schedule/new']:
        assert c.get(path).status_code==200,path
    sid=show_id(app)
    with app.app_context():
        show=db.session.get(Session,sid)
        values={'city':show.cinema.city,'cinema_id':show.cinema_id,'hall_id':show.hall_id,'film_id':show.film_id,'start':show.session_datetime.isoformat(),'price':'150'}
    values['csrf_token']=csrf(c)
    assert c.post('/admin/schedule/new',data=values).status_code==400

def test_manager_scope_sale(app):
    c=app.test_client();sign_in(c,'manager')
    assert c.get('/manager/').status_code==200
    assert c.get('/admin/').status_code==403
    sid=show_id(app)
    assert c.get('/manager/?session_id='+str(sid)).status_code==200
    result=c.post('/manager/sale',data={'session_id':sid,'selected_seats':json.dumps([{'row':2,'col':7}]),'payment_method':'cash','csrf_token':csrf(c)})
    assert result.status_code==302,result.data
    oid=result.location.rsplit('/',1)[-1]
    with app.app_context():
        order=db.session.get(Order,oid)
        assert order.status=='paid' and order.payment_method=='cash' and order.fiscal_status=='not_fiscalized'
    assert c.get('/ticket_pdf?order_id='+oid).status_code==200
    result=c.post('/manager/sale',data={'session_id':show_id(app,'Львів'),'selected_seats':json.dumps([{'row':2,'col':7}]),'payment_method':'card','csrf_token':csrf(c)})
    assert result.status_code==403

def test_seed_idempotence(app):
    from seed_demo import seed
    with app.app_context():
        counts=[model.query.count() for model in [Cinema,Hall,Film,Session,Product,Category,User,Order,Ticket,SeatReservation]]
        seed()
        assert counts==[model.query.count() for model in [Cinema,Hall,Film,Session,Product,Category,User,Order,Ticket,SeatReservation]]

def test_admin_edit_forms(app):
    c=app.test_client();sign_in(c,'admin')
    for name in ['film','session','cinema','hall','image','user','product','category']:
        response=c.get('/admin/'+name+'/new/')
        assert response.status_code==200,(name,re.findall(r'role="alert">(.*?)</p>',response.data.decode()))

def test_admin_create_update_product(app):
    c=app.test_client();sign_in(c,'admin')
    with app.app_context():
        category=Category.query.first().id
    values={'name':'Тестовий мерч','description':'Створено інтеграційним тестом','category':str(category),'price':'325.50','stock':'8','image':'/static/img/merch.svg','active':'y','csrf_token':csrf(c)}
    response=c.post('/admin/product/new/',data=values)
    assert response.status_code==302,response.data[-1000:]
    with app.app_context():
        product=Product.query.filter_by(name='Тестовий мерч').one()
        assert product.price==Decimal('325.50') and product.stock==8
        pid=product.id
    values.update(price='349.50',csrf_token=csrf(c))
    assert c.post('/admin/product/edit/?id='+str(pid),data=values).status_code==302
    with app.app_context():
        assert db.session.get(Product,pid).price==Decimal('349.50')

def test_pickup_payment_and_scope(app):
    customer=app.test_client();sign_in(customer)
    with app.app_context():
        pid=Product.query.first().id
        cinema=Cinema.query.filter_by(city='Київ').first().cinema_id
    assert customer.post('/cart/update',data={'product_id':pid,'quantity':1,'csrf_token':csrf(customer)}).status_code==302
    result=post(customer,'/checkout',{'fulfillment':'pickup','payment_method':'cinema','name':'Гість','phone':'0500000000','cinema_id':str(cinema)})
    assert result.status_code==302
    oid=result.location.rsplit('/',1)[-1]
    with app.app_context():
        assert db.session.get(Order,oid).status=='pending'
    manager=app.test_client();sign_in(manager,'manager')
    assert manager.get('/manager/shop').status_code==200
    for _ in range(2):
        assert manager.post('/manager/shop/'+oid+'/collect',data={'payment_method':'cash','csrf_token':csrf(manager)}).status_code==302
    with app.app_context():
        order=db.session.get(Order,oid)
        assert order.status=='paid' and order.fulfillment_status=='collected' and order.payment_method=='cash' and order.is_demo

def test_late_liqpay_payment_does_not_issue_ticket(app):
    import base64,hashlib,json
    c=app.test_client();sign_in(c)
    result=post(c,'/buy_ticket',{'session_id':show_id(app),'tickets':[{'row':4,'col':5}]})
    oid=result.json['order_id'];amount=result.json['total']
    with app.app_context():
        db.session.get(Order,oid).expires_at=datetime.now()-timedelta(minutes=1)
        db.session.commit()
    previous={k:app.config[k] for k in ['PAYMENT_DEMO_MODE','LIQPAY_PUBLIC_KEY','LIQPAY_PRIVATE_KEY','PUBLIC_BASE_URL']}
    app.config.update(PAYMENT_DEMO_MODE=False,LIQPAY_PUBLIC_KEY='test-public',LIQPAY_PRIVATE_KEY='test-private',PUBLIC_BASE_URL='https://example.local')
    payload={'version':7,'public_key':'test-public','action':'pay','order_id':oid,'payment_id':777002,'status':'success','amount':amount,'currency':'UAH'}
    encoded=base64.b64encode(json.dumps(payload).encode()).decode()
    digest=base64.b64encode(hashlib.sha3_256(('test-private'+encoded+'test-private').encode()).digest()).decode()
    try:
        assert c.post('/payments/liqpay/callback',data={'data':encoded,'signature':digest}).status_code==200
        with app.app_context():
            assert db.session.get(Order,oid).status=='payment_review'
            assert not db.session.get(Order,oid).tickets
            assert PaymentReceipt.query.filter_by(order_id=oid).one().status=='needs_review'
    finally:
        app.config.update(previous)

def test_liqpay_signature_callback_idempotence(app):
    import base64,hashlib,json
    from liqpay_payment import signature
    c=app.test_client();sign_in(c);sid=show_id(app)
    response=post(c,'/buy_ticket',{'session_id':sid,'tickets':[{'row':3,'col':4}]})
    oid=response.json['order_id'];amount=response.json['total']
    previous={key:app.config[key] for key in ['PAYMENT_DEMO_MODE','LIQPAY_PUBLIC_KEY','LIQPAY_PRIVATE_KEY','PUBLIC_BASE_URL']}
    app.config.update(PAYMENT_DEMO_MODE=False,LIQPAY_PUBLIC_KEY='test-public',LIQPAY_PRIVATE_KEY='test-private',PUBLIC_BASE_URL='https://example.local')
    payload={'version':7,'public_key':'test-public','action':'pay','order_id':oid,'payment_id':777001,'status':'success','amount':amount,'currency':'UAH'}
    def callback(values,valid=True):
        encoded=base64.b64encode(json.dumps(values).encode()).decode()
        digest=base64.b64encode(hashlib.sha3_256(('test-private'+encoded+'test-private').encode()).digest()).decode() if valid else 'forged'
        return c.post('/payments/liqpay/callback',data={'data':encoded,'signature':digest})
    try:
        assert c.post('/payment/'+oid+'/liqpay',data={'csrf_token':csrf(c)}).status_code==200
        assert callback(payload,False).status_code==403
        assert callback({**payload,'amount':'1.00'}).status_code==409
        assert callback({**payload,'currency':'USD'}).status_code==409
        assert callback({**payload,'status':'processing'}).status_code==200
        with app.app_context():
            assert not db.session.get(Order,oid).tickets
        assert callback(payload).status_code==200
        assert callback(payload).status_code==200
        with app.app_context():
            assert Ticket.query.filter_by(order_id=oid).count()==1
            assert PaymentReceipt.query.filter_by(order_id=oid).count()==1
        assert callback({**payload,'status':'reversed'}).status_code==200
        assert c.get('/ticket_pdf?order_id='+oid).status_code==403
    finally:
        app.config.update(previous)

def test_official_liqpay_v7_signature_vector(app):
    import base64
    from liqpay_payment import signature
    with app.app_context():
        original=app.config['LIQPAY_PRIVATE_KEY']
        app.config['LIQPAY_PRIVATE_KEY']='a4825234f4bae72a0be04eafe9e8e2bada209255'
        try:
            encoded='eyJwdWJsaWNfa2V5IjoiaTAwMDAwMDAwIiwidmVyc2lvbiI6NywiYWN0aW9uIjoicGF5IiwiYW1vdW50IjoiMyIsImN1cnJlbmN5IjoiVUFIIiwiZGVzY3JpcHRpb24iOiJ0ZXN0Iiwib3JkZXJfaWQiOiIwMDAwMDEifQ=='
            assert signature(encoded)=='0adgJ8F2Ds5HCVkcz4AlmdLMRoIJf7IxsL3QmeFRz/s='
        finally:
            app.config['LIQPAY_PRIVATE_KEY']=original

def test_parallel_halls_and_paid_session_immutability(app):
    c=app.test_client();sign_in(c,'admin')
    with app.app_context():
        cinema=Cinema.query.filter_by(city='Київ').first()
        halls=Hall.query.filter_by(cinema_id=cinema.cinema_id).order_by(Hall.id).all()
        film=Film.query.first()
        values={'city':cinema.city,'cinema_id':str(cinema.cinema_id),'film_id':str(film.film_id),'start':(datetime.now()+timedelta(days=10)).replace(hour=12,minute=0,second=0,microsecond=0).isoformat(),'price':'175'}
        hall_ids=[h.id for h in halls]
    for hall_id in hall_ids[:2]:
        assert c.post('/admin/schedule/new',data={**values,'hall_id':hall_id,'csrf_token':csrf(c)}).status_code==302
    with app.app_context():
        paid=Session.query.join(Ticket).first()
        sid=paid.session_id;price=paid.price
        edit={'film':str(paid.film_id),'cinema':str(paid.cinema_id),'hall':str(paid.hall_id),'session_datetime':paid.session_datetime.strftime('%Y-%m-%d %H:%M:%S'),'price':str(price+20),'vip_multiplier':str(paid.vip_multiplier)}
    edit['csrf_token']=csrf(c)
    response=c.post('/admin/session/edit/?id='+str(sid),data=edit)
    assert response.status_code==200
    with app.app_context():
        assert db.session.get(Session,sid).price==price
