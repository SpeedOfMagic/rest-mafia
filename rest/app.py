import base64
import secrets
import sqlite3

from flask import Flask, request, render_template_string, make_response
from rest.profile_dao import Profile, ProfileDao
from rest.pdf_report import generate_pdf_by_profile
from hashlib import sha256
import jwt


app = Flask(__name__)
dao = ProfileDao()
secret = secrets.token_hex(16)


def get_hash(password):
    return sha256(password.encode()).hexdigest()


def get_login_if_authorized():
    if 'jwt' in request.cookies:
        jwt_token = request.cookies['jwt']
        try:
            login_pass = jwt.decode(jwt_token, secret, algorithms=["HS256"])
        except jwt.DecodeError:
            return None
        if 'login' in login_pass and 'password' in login_pass:
            login_profile = dao.lookup_profile(login_pass['login'])
            if login_profile is not None and login_profile.password == get_hash(login_pass['password']):
                return login_profile.login
    return None


def render_page(page, authorized_login=None, use_param=False, **context):
    template = open('templates/base.html').read().replace('{main}', open(f'templates/{page}').read())
    context['authorized_login'] = authorized_login if use_param else get_login_if_authorized()
    return render_template_string(template, **context)


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

    jwt_token = jwt.encode({'login': login, 'password': request.form['password']}, secret, algorithm="HS256")
    resp = make_response(render_page('response.html', login, True, reason='Authorization successful!'))
    resp.set_cookie('jwt', jwt_token)
    return resp


@app.route('/profile/<string:login>')
def profile(login):
    cur_profile = dao.lookup_profile(login)
    if cur_profile is None:
        return render_page('response.html', reason='No such profile exists'), 400
    base64image = base64.b64encode(cur_profile.image).decode()
    return render_page('profile.html', **vars(cur_profile), base64image=base64image)


@app.route('/edit/<string:login>', methods=['GET'])
def edit(login):
    if login is None or login == '':
        return render_page('response.html', reason='Invalid login'), 400
    if get_login_if_authorized() != login:
        return render_page('response.html', reason='You cannot edit profile of another account!'), 403
    return render_page('edit.html', login=login)


@app.route('/edit/<string:login>', methods=['POST'])
def edit_post(login):
    if login is None or login == '':
        return render_page('response.html', reason='Invalid login'), 400
    if get_login_if_authorized() != login:
        return render_page('response.html', reason='You cannot edit profile of another account!'), 403

    password = get_hash(request.form['password']) if request.form['password'] else None
    name = request.form['name'] if request.form['name'] else None
    image = request.files['image'].stream.read() if 'image' in request.files else None
    gender = request.form['gender'] if request.form['gender'] else None
    mail = request.form['mail'] if request.form['mail'] else None
    dao.modify_profile(login, password=password, name=name, image=image, gender=gender, mail=mail)
    return render_page('response.html', reason='Profile updated')


# TODO Handle for submitting game result
# TODO JWT for game part


@app.route('/logout')
def logout():
    if get_login_if_authorized() is None:
        return render_page('response.html', reason='You are already logged out')
    resp = make_response(render_page('response.html', None, True, reason='You have successfully logged out'))
    resp.set_cookie('jwt', '')
    return resp


@app.route('/report/<string:login>.pdf')
def generate_pdf(login):
    # TODO Use rabbitmq to do this shit
    cur_profile = dao.lookup_profile(login)
    pdf = generate_pdf_by_profile(cur_profile)
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename={login}.pdf'
    return response


@app.route('/ico.png')
def ico():
    return open('templates/ico.png', 'rb').read()


@app.route('/favicon.ico')
def fav():
    return open('templates/favicon.ico', 'rb').read()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
