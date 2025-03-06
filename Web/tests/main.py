from flask import *

app = Flask(__name__)



@app.route('/prices.txt')
def serve_prices():
    return send_from_directory('.', 'prices.txt')

@app.route('/seating.txt')
def serve_seating():
    return send_from_directory('.', 'seating.txt')


@app.route('/')
def hello_world():

    return render_template('BookTest.html')
# Маршрут для отримання вибраних місць
@app.route('/buy', methods=['POST'])
def buy_tickets():
    data = request.json  # Отримуємо JSON з фронтенду
    print("Отримані місця:", data)

    # Тут можна зберігати у базі даних або текстовому файлі
    with open("booked_seats.json", "w", encoding="utf-8") as f:
        import json
        json.dump(data, f, indent=4, ensure_ascii=False)

    return jsonify({"status": "success", "message": "Квитки успішно заброньовані!"})

if __name__ == '__main__':
    app.run(debug=True, host="192.168.31.36")