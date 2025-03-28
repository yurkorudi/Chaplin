from extensions import db
from models import *
from flask import jsonify, request

def list_to_dict(data):
    result = {}
    for item in data:
        name = item['name']
        result[name] = {key: value for key, value in item.items() if key != 'name'}
    return result



def add_image(type, path):
    try:
        existing_image = Image.query.filter_by(path=path).first()
        if existing_image:
            # print("###########################################>> IMAGE ALREADY EXIST <<###########################################")
            return jsonify({"message": "Image already exists"}), 200

        new_image = Image(type=type, path=path)
        db.session.add(new_image)
        db.session.commit()
        return jsonify({"message": "Image added successfully"}), 201
    except Exception as e:
        db.session.rollback()
        # print("###########################################>> IMAGE NOT EXISTING CAPTURED - FAILED ADDING IMAGE <<###########################################")
        # print("ERROR>> ", e)
        return jsonify({"error": str(e)}), 500

def get_images(id=False):
    if id == False:
        images = Image.query.all()
        return [{"id": img.image_id, "type": img.type, "path": img.path} for img in images]
    else:
        image = Image.query.filter_by(image_id=id).first()
        if image:
            return {
                "id":image.image_id,
                "type":image.type,
                "path":image.path
            }
        else:
            return {"error": f"Film with name '{id}' not found."}



def add_user(first_name, last_name, email, login, password, bought_tickets_summary):
    try:

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            print('massage: User already exists')
            return jsonify({"message": "User already exists"}), 200

        new_user = User(
            first_name=first_name,
            last_name=last_name,
            email=email,
            login=login,
            password=password,
            bought_tickets_summary=bought_tickets_summary,
            date_of_creation=datetime.now()
        )
        db.session.add(new_user)
        db.session.commit()
        print('massage: User added successfully')
        return jsonify({"message": "User added successfully"}), 200
    except Exception as e:
        db.session.rollback()
        print('error: ', e)
        return jsonify({"error": str(e)}), 500


def get_users():
    users = User.query.all()
    return [{"user_id": u.id, "email" : u.email, "login" : u.login, "password" : u.password, "name": f"{u.first_name} {u.last_name}", "tickets": u.bought_tickets_summary} for u in users]


def add_cinema(name, location, contact_phone_number, work_schedule, instagram_link):
    try:

        existing_cinema = Cinema.query.filter_by(name=name, location=location).first()
        if existing_cinema:
            return jsonify({"message": f"Cinema '{name}' at '{location}' already exists"}), 200

        new_cinema = Cinema(
            name=name,
            location=location,
            contact_phone_number=contact_phone_number,
            work_schedule=work_schedule,
            instagram_link=instagram_link
        )
        db.session.add(new_cinema)
        db.session.commit()
        return jsonify({"message": "Cinema added successfully"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


def get_cinemas():
    cinemas = Cinema.query.all()
    return [{"cinema_id": c.cinema_id, "name": c.name, "location": c.location,
             "contact_phone_number": c.contact_phone_number, "work_schedule": c.work_schedule,
             "instagram_link": c.instagram_link} for c in cinemas]


def add_session(film_id, cinema_id, session_datetime, session_duration):
    try:
        existing_session = Session.query.filter_by(film_id=film_id, cinema_id=cinema_id, session_datetime=session_datetime).first()
        if existing_session:
            return jsonify({"message": "Session already exists"}), 200

        new_session = Session(
            film_id=film_id,
            cinema_id=cinema_id,
            session_datetime=session_datetime,
            session_duration=session_duration
        )
        db.session.add(new_session)
        db.session.commit()
        return jsonify({"message": "Session added successfully"}), 201
    except Exception as e:
        db.session.rollback()
        print("###########################################>> SESSION NOT EXISTING CAPTURED - FAILED ADDING SESSIONS <<###########################################")
        print("ERROR>> ", e)
        return jsonify({"error": str(e)}), 500



def get_sessions(film_id=False):
    if film_id == False:    
        sessions = Session.query.all()
        return [{"session_id": s.session_id, "film_id": s.film_id, "cinema_id": s.cinema_id,
                "session_datetime": s.session_datetime, "session_duration": s.session_duration} for s in sessions]

    else: 
        sessions = Session.query.filter_by(film_id=film_id)
        if sessions:
            return[{ 
            "session_id" : ss.session_id,
            "film_id" : ss.film_id,
            "cinema_id" : ss.cinema_id,
            "session_datetime" : ss.session_datetime,
            "session_duration" : ss.session_duration
            }for ss in sessions]
        else:
            return {"error": f"Session with film_ID '{film_id}' not found."}




def add_film(name, genre, description, release_start_date, release_end_date, director, actors, duration, age, image_id):
    try:

        existing_image = Image.query.filter_by(image_id=image_id).first()
        if not existing_image:
            print({"error": f"Image with id {image_id} does not exist"})
            return jsonify({"error": f"Image with id {image_id} does not exist"}), 400

 
        existing_film = Film.query.filter_by(name=name, release_start_date=release_start_date).first()
        if existing_film:
            return jsonify({"message": f"Film '{name}' with release start date '{release_start_date}' already exists"}), 200

        new_film = Film(
            name=name,
            genre=genre,
            description=description,
            release_start_date=release_start_date,
            release_end_date=release_end_date,
            director=director,
            actors=actors,
            duration=duration,
            age=age,
            image_id=image_id
        )
        db.session.add(new_film)
        db.session.commit()
        return jsonify({"message": "Film added successfully"}), 201
    except Exception as e:
        print(e)
        db.session.rollback()
        return jsonify({"error": str(e)}), 500



def get_films(name=False):
    if name == False:
        films = Film.query.all()
        return [{"film_id": f.film_id, "name": f.name, "genre": f.genre, "description": f.description,
                "release_start_date": f.release_start_date, "release_end_date": f.release_end_date,
                "director": f.director, "actors": f.actors, "duration": f.duration, "image_id": f.image_id, "age": f.age} for f in films]
    else:
        film = Film.query.filter_by(name=name).first()
        if film:
            return {
                "film_id": film.film_id,
                "name": film.name,
                "genre": film.genre,
                "description": film.description,
                "release_start_date": film.release_start_date,
                "release_end_date": film.release_end_date,
                "director": film.director,
                "actors": film.actors,
                "duration": film.duration,
                "age": film.age,
                "image_id": film.image_id
            }
        else:
            return {"error": f"Film with name '{name}' not found."}


def add_seat(session_id, row, busy):
    try:
        # Check if the session exists
        existing_session = Session.query.filter_by(session_id=session_id).first()
        if not existing_session:
            return jsonify({"error": f"Session with id {session_id} does not exist"}), 400

        # Check if the seat already exists
        existing_seat = Seat.query.filter_by(session_id=session_id, row=row).first()
        if existing_seat:
            return jsonify({"message": "Seat already exists"}), 200

        new_seat = Seat(session_id=session_id, row=row, busy=busy)
        db.session.add(new_seat)
        db.session.commit()
        return jsonify({"message": "Seat added successfully"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

def get_seats(session_id = False):
    if session_id == False:
        seats = Seat.query.all()
        return [{"seat_id": s.seat_id, "session_id": s.session_id, "row": s.row, "busy": s.busy} for s in seats]
    else:
        seats = Seat.query.filter_by(session_id=session_id)
        return [{"seat_id": s.seat_id, "session_id": s.session_id, "row": s.row, "busy": s.busy} for s in seats]

def add_ticket(user_phone_number, seat_id, session_id, date_of_purchase=None, user_id=None):
    try:

        existing_ticket = Ticket.query.filter_by(user_phone_number=user_phone_number, seat_id=seat_id, session_id=session_id, user_id=user_id ).first()
        if existing_ticket:
            return jsonify({"message": "Ticket already exists"}), 200

        new_ticket = Ticket(
            user_phone_number=user_phone_number,
            seat_id=seat_id,
            session_id=session_id,
            user_id=user_id,  
            date_of_purchase=date_of_purchase or datetime.utcnow()
        )
        db.session.add(new_ticket)
        db.session.commit()
        return jsonify({"message": "Ticket added successfully"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

def get_tickets():
    tickets = Ticket.query.all()
    return [{"ticket_id": t.ticket_id, "user_phone_number": t.user_phone_number,
             "seat_id": t.seat_id, "session_id": t.session_id, "user_id": t.user_id,
             "date_of_purchase": t.date_of_purchase} for t in tickets]


