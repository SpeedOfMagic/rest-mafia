from flask import Flask


app = Flask(__name__)


@app.route('/')
def index():
    return open('templates/index.html').read()


@app.route('/all_profiles')
def all_profiles():
    return open('templates/all_profiles.html').read()


@app.route('/register')
def register():
    return open('templates/register.html').read()


@app.route('/authorize')
def authorize():
    return open('templates/authorize.html').read()


@app.route('/favicon.ico')
def fav():
    return open('templates/favicon.ico', 'rb').read()


@app.route('/profile/<string:login>')
def profile(login):
    print(login)
    return open('templates/profile.html').read()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
