import sqlite3

from flask import Flask, request, render_template
from rest.profile_dao import Profile, ProfileDao
from hashlib import sha256


app = Flask(__name__)
dao = ProfileDao()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/all_profiles')
def all_profiles():
    return render_template('all_profiles.html', all_profiles=dao.get_all_logins())


@app.route('/register', methods=['GET'])
def register_get():
    return render_template('register.html')


@app.route('/register', methods=['POST'])
def register_post():
    new_profile = Profile(login=request.form['login'], password=sha256(request.form['password'].encode()).hexdigest())
    try:
        dao.insert_profile(new_profile)
    except sqlite3.IntegrityError:
        return render_template('failed.html', reason='Registration failed, since such user already exists'), 400
    return render_template('registration_complete.html')


@app.route('/authorize')
def authorize():
    return render_template('authorize.html')


@app.route('/profile/<string:login>')
def profile(login):
    cur_profile = dao.lookup_profile(login)
    if cur_profile is None:
        return render_template('fail.html', reason='No such profile exists')
    return render_template('profile.html', **vars(cur_profile))


@app.route('/ico.png')
def ico():
    return open('templates/ico.png', 'rb').read()


@app.route('/favicon.ico')
def fav():
    return open('templates/favicon.ico', 'rb').read()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
