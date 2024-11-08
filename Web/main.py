from flask import *
from user_agents import parse
import json
from modls import JSN
from modls import Film

app = Flask(__name__)

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
    my_file = JSN(json=json, filepath='mdb.json', type="0")
    movie = Film(filmname='trans', json_file=my_file.dirty_data, city='lviv')


    if user_location == []:
        a = location()

    return render_template('Movie.html', city = "", cities = cities, movie_info = movie.ret_filmfile())
        


@app.route('/About.html')
def about():
    return render_template('About.html')


if __name__ == '__main__':
    app.run(debug=True, host= '127.0.0.1')     