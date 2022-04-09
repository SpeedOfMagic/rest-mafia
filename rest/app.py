from flask import Flask, request, Markup


app = Flask(__name__)


@app.route('/')
def index():
    return open('templates/index.html').read()


@app.route('/all_profiles')
def all_profiles():
    return open('templates/all_profiles.html').read()


@app.route('/register', methods=['GET'])
def register_get():
    return open('templates/register.html').read()


@app.route('/register', methods=['POST'])
def register_post():
    print('POSTED!')
    return open('templates/registration_complete.html').read()


@app.route('/authorize')
def authorize():
    return open('templates/authorize.html').read()


@app.route('/profile/<string:login>')
def profile(login):
    print(login)
    return open('templates/profile.html').read()


@app.route('/ico.png')
def ico():
    return open('templates/ico.png', 'rb').read()


@app.route('/favicon.ico')
def fav():
    return open('templates/favicon.ico', 'rb').read()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
