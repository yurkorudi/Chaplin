"""Optional LiqPay API v7: server-signed checkout and authenticated callback.

Official protocol: https://www.liqpay.ua/uk/doc/api/callback
Version 7 uses SHA3-256. No legacy SHA1 fallback or redirect confirmation.
"""
import base64
import binascii
import hashlib
import hmac
import json
from decimal import Decimal,InvalidOperation
from urllib.parse import urlsplit
from flask import abort,current_app,request,render_template
from werkzeug.exceptions import HTTPException
from extensions import db
from models import Order,PaymentReceipt,Session,SeatReservation,Product

def enabled():
    config=current_app.config
    base=urlsplit(config['PUBLIC_BASE_URL'])
    return bool(not config['PAYMENT_DEMO_MODE'] and config['LIQPAY_PUBLIC_KEY'] and config['LIQPAY_PRIVATE_KEY'] and base.scheme=='https' and base.netloc and not base.query and not base.fragment)

def signature(data):
    secret=current_app.config['LIQPAY_PRIVATE_KEY']
    return base64.b64encode(hashlib.sha3_256((secret+data+secret).encode('utf-8')).digest()).decode('ascii')

def checkout(order_id):
    from commerce import owned_order,now,money
    if not enabled():
        abort(503,description='Реальну оплату LiqPay не налаштовано.')
    order=owned_order(order_id,lock=True)
    if order.status!='pending' or order.payment_method!='online' or order.expires_at and order.expires_at<=now():
        abort(409,description='Замовлення недоступне для оплати.')
    total=sum((item.price*item.quantity for item in order.items),Decimal(0))
    if total!=order.total or total<=0:
        abort(409)
    for item in order.items:
        if order.kind=='tickets':
            show=Session.query.filter_by(session_id=item.session_id).with_for_update().one()
            hold=SeatReservation.query.filter_by(order_id=order.id,session_id=item.session_id,row_index=item.row_index,column_index=item.column_index).first()
            if not hold or hold.expires_at<=now() or show.session_datetime<=now():
                abort(409,description='Резервування вже недійсне.')
            cell=show.hall.structure[item.row_index][item.column_index]
            expected=money(show.price*(show.vip_multiplier if cell==2 else Decimal(1)))
            if expected!=item.price:
                abort(409,description='Ціна сеансу змінилася.')
        else:
            product=Product.query.filter_by(id=item.product_id).with_for_update().one()
            if product.price!=item.price:
                abort(409,description='Ціна товару змінилася.')
    base=current_app.config['PUBLIC_BASE_URL']
    payload={'version':7,'public_key':current_app.config['LIQPAY_PUBLIC_KEY'],'action':'pay','amount':str(money(order.total)),'currency':order.currency,'description':f'Chaplin Cinema / {order.id}','order_id':order.id,'language':'uk','server_url':base+'/payments/liqpay/callback','result_url':base+'/payment/'+order.id}
    if order.expires_at:
        payload['expired_date']=order.expires_at.astimezone().astimezone(__import__('datetime').timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    encoded=base64.b64encode(json.dumps(payload,ensure_ascii=False,separators=(',',':')).encode()).decode('ascii')
    return render_template('liqpay_checkout.html',order=order,payment_data=encoded,payment_signature=signature(encoded))

def callback():
    from commerce import complete_order
    if not enabled():
        abort(503)
    encoded=request.form.get('data','');received_signature=request.form.get('signature','')
    if not encoded or len(encoded)>24000 or not hmac.compare_digest(signature(encoded).encode('ascii'),received_signature.encode('utf-8')):
        abort(403)
    try:
        payload=json.loads(base64.b64decode(encoded,validate=True).decode('utf-8'))
        if not isinstance(payload,dict):
            raise ValueError('Expected an object.')
        amount=Decimal(str(payload.get('amount')))
        if not amount.is_finite():
            raise ValueError('Invalid amount.')
    except (ValueError,binascii.Error,UnicodeError,InvalidOperation):
        abort(400)
    if payload.get('public_key')!=current_app.config['LIQPAY_PUBLIC_KEY'] or str(payload.get('version'))!='7' or payload.get('action')!='pay':
        abort(403)
    order=Order.query.filter_by(id=str(payload.get('order_id',''))).with_for_update().first_or_404()
    if amount!=order.total or payload.get('currency')!=order.currency or order.payment_method!='online':
        abort(409)
    status=str(payload.get('status',''))
    if status not in ('success','reversed'):
        # Pending, failed and verification statuses cannot issue tickets.
        return 'ok',200
    reference=str(payload.get('payment_id',''))
    if not reference.isdigit() or len(reference)>80:
        abort(400)
    reference='liqpay:'+reference
    receipt=PaymentReceipt.query.filter_by(order_id=order.id).first()
    if receipt:
        if receipt.provider_reference!=reference:
            abort(409)
        if status=='reversed':
            receipt.status='reversed';order.status='payment_review'
            db.session.commit()
        return 'ok',200
    if PaymentReceipt.query.filter_by(provider_reference=reference).first():
        abort(409)
    receipt=PaymentReceipt(order_id=order.id,provider_reference=reference,amount=amount,currency=order.currency,status=status)
    db.session.add(receipt)
    if status=='reversed' or order.status!='pending':
        receipt.status='needs_review';order.status='payment_review'
    else:
        try:
            with db.session.begin_nested():
                complete_order(order)
        except HTTPException as error:
            if error.code!=409:
                raise
            # A late successful bank callback must never steal a released seat.
            receipt.status='needs_review';order.status='payment_review'
            current_app.logger.warning('Verified payment requires review for order %s',order.id)
    db.session.commit()
    return 'ok',200
