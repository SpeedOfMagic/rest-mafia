import secrets
import sqlite3

from flask import Flask, request, render_template_string, make_response
from rest.profile_dao import Profile, ProfileDao
from hashlib import sha256
import jwt


app = Flask(__name__)
dao = ProfileDao()
secret = secrets.token_hex(16)


def get_hash(password):
    return sha256(password.encode()).hexdigest()


def render_page(page, **context):
    template = open('templates/base.html').read().replace('{main}', open(f'templates/{page}').read())
    context['login'] = get_login_if_authorized()
    return render_template_string(template, **context)


def get_login_if_authorized():
    if 'jwt' in request.cookies:
        jwt_token = request.cookies['jwt']
        try:
            login_pass = jwt.decode(jwt_token, secret, algorithms=["HS256"])
        except jwt.DecodeError as e:
            print(e)
            return None
        if 'login' in login_pass and 'password' in login_pass:
            login_profile = dao.lookup_profile(login_pass['login'])
            if login_profile is not None and login_profile.password == get_hash(login_pass['password']):
                return login_profile.login
    return None


@app.route('/')
def index():
    return render_page('index.html')


@app.route('/all_profiles')
def all_profiles():
    return render_page('all_profiles.html', all_profiles=dao.get_all_logins())


@app.route('/register', methods=['GET'])
def register_get():
    if get_login_if_authorized() is not None:
        return render_page('response.html', reason='You cannot register since you are already logged in'), 403
    return render_page('register.html')


@app.route('/register', methods=['POST'])
def register_post():
    if get_login_if_authorized() is not None:
        return render_page('response.html', reason='You cannot register since you are already logged in'), 403

    new_profile = Profile(login=request.form['login'], password=get_hash(request.form['password']))
    try:
        dao.insert_profile(new_profile)
    except sqlite3.IntegrityError:
        return render_page('response.html', reason='Registration failed, since such user already exists'), 400
    return render_page('response.html', reason='Registration is complete!')


@app.route('/authorize', methods=['GET'])
def authorize():
    if get_login_if_authorized() is not None:
        return render_page('response.html', reason='You cannot authorize since you are already logged in'), 403
    return render_page('authorize.html')


@app.route('/authorize', methods=['POST'])
def authorize_post():
    if get_login_if_authorized() is not None:
        return render_page('response.html', reason='You cannot authorize since you are already logged in'), 403

    login, password = request.form['login'], get_hash(request.form['password'])
    cur_profile = dao.lookup_profile(login)
    if cur_profile is None:
        return render_page('response.html', reason='No such profile exists'), 400
    if cur_profile.password != password:
        return render_page('response.html', reason='Password is incorrect'), 400
    resp = make_response(render_page('response.html', reason='Authorization successful!'))

    jwt_token = jwt.encode({'login': login, 'password': request.form['password']}, secret, algorithm="HS256")
    resp.set_cookie('jwt', jwt_token)
    return resp


@app.route('/profile/<string:login>')
def profile(login):
    cur_profile = dao.lookup_profile(login)
    if cur_profile is None:
        return render_page('response.html', reason='No such profile exists'), 400
    # TODO Display image
    return render_page('profile.html', **vars(cur_profile))


# TODO Edit profile
# TODO Generate PDF
# TODO Check permissions for edit
# TODO Handle for submitting game result


@app.route('/logout')
def logout():
    pass


@app.route('/ico.png')
def ico():
    return open('templates/ico.png', 'rb').read()


@app.route('/favicon.ico')
def fav():
    return open('templates/favicon.ico', 'rb').read()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
