from flask import *

app = Flask(__name__)


@app.route('/page')
def page():
    return render_template ('Main.html')


@app.route('/ticket', methods=['POST'])
def ticket():
    print("Request Headers:", request.headers)
    print("Request Content-Type:", request.content_type)
    
    # Для JSON
    if request.content_type == 'application/json':
        try:
            data = request.get_json()  # Отримуємо дані як JSON
            print("Received JSON:", data)
            return jsonify({"message": "Seat selection received!", "status": "success"}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 400
    else:
        return jsonify({"error": "Invalid Content-Type"}), 415


if __name__ == "__main__":
    app.run(debug=True)