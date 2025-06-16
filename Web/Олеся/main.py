from flask import *

app = Flask(__name__)


@app.route('/')
def index():
    print ('index')
    
    return redirect('/home')



@app.route('/news')
def news():
    print ('helloworld')

    return render_template('release_page.html')


@app.route('/home')
def home():
    print ('home')
    
    return render_template('index.html')


@app.route('/login')
def login():
    print ('login')
    
    return render_template('login.html')


@app.route('/news2')
def news2():
    print ('news2')
    
    return render_template('news2.html')

if __name__ == "__main__":
    app.run(debug=True)