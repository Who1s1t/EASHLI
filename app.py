import datetime
import random

from flask import Flask, render_template, redirect, make_response, session
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
import secrets
import string
from data import db_session, links_resourse
from data.links import Link
from data.users import User
from data.links import Link
from data.transitions import Transition
from forms.password import Password
from forms.nologinlink import NoLoginLinkForm
from forms.user import RegisterForm, LoginForm
from flask_restful import reqparse, abort, Api, Resource

app = Flask(__name__)
api = Api(app)
login_manager = LoginManager()
login_manager.init_app(app)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(
    days=30
)


def generate_alphanum_crypt_string(length):
    letters_and_digits = string.ascii_letters + string.digits
    crypt_rand_string = ''.join(secrets.choice(
        letters_and_digits) for i in range(length))
    return crypt_rand_string


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route("/<_link>", methods=['GET', 'POST'])
def red(_link):
    db_sess = db_session.create_session()
    link = db_sess.query(Link).filter(Link.alias == _link).first()
    if link.hashed_password:
        form = Password()
        if form.validate_on_submit():
            if link.check_password(form.password.data):
                transition = Transition()
                link.transition.append(transition)
                db_sess.commit()
                return redirect(link.link)
            return render_template("password.html", form=form, title="Проверка", message="Неверный пароль!")
        return render_template("password.html", form=form, title="Проверка")
    transition = Transition()
    transition.link_id = link
    link.transition.append(transition)
    db_sess.commit()
    return redirect(link.link)


@app.route("/", methods=['GET', 'POST'])
def index():
    form = NoLoginLinkForm()
    db_sess = db_session.create_session()
    if form.validate_on_submit():
        if not db_sess.query(Link).filter(Link.alias == form.alias.data).first():
            link = Link()
            link.set_link(form.link.data)
            if not form.alias.data:
                link.alias = generate_alphanum_crypt_string(5)
            else:
                link.alias = form.alias.data
            if form.password.data:
                link.set_password(form.password.data)
            if current_user.is_authenticated:
                link.user_id = current_user.id
            else:
                link.user_id = session.get('temp_id', 0)
            db_sess.add(link)
            db_sess.commit()
            return redirect("/")
        if current_user.is_authenticated:
            links = db_sess.query(Link).filter(Link.user_id == current_user.id)
        else:
            links = db_sess.query(Link).filter(Link.user_id == session.get('temp_id', -1))
        return render_template("index.html", form=form, links=links, title="Главная", message="Такой алиас уже есть!")
    if not session.get('temp_id', 0):
        session["temp_id"] = random.randint(10000000, 100000000)
    session.permanent = True
    if current_user.is_authenticated:
        links = db_sess.query(Link).filter(Link.user_id == current_user.id)
    else:
        links = db_sess.query(Link).filter(Link.user_id == session.get('temp_id', -1))
    return render_template("index.html", form=form, links=links, title="Главная")


@app.route("/dashboard", methods=['GET', 'POST'])
def dashboard():
    if current_user.is_authenticated:
        db_sess = db_session.create_session()
        links = db_sess.query(Link).filter(Link.user_id == current_user.id)
        day = 0
        month = 0
        _all = 0
        all_link = 0
        for link in links:
            transitions = db_sess.query(Transition).filter(Transition.link_id == link.id)
            for transit in transitions:
                _all += 1
            transitions = db_sess.query(Transition).filter(Transition.link_id == link.id).filter(
                Transition.created_date > datetime.datetime.now() - datetime.timedelta(days=1))
            for transit in transitions:
                day += 1
            transitions = db_sess.query(Transition).filter(Transition.link_id == link.id).filter(
                Transition.created_date > datetime.datetime.now() - datetime.timedelta(weeks=4))
            for transit in transitions:
                month += 1
            all_link += 1
        return render_template("dashboard.html", title="Cтатистика", day=day, month=month, all=_all, all_link=all_link)
    return redirect('/login')


@app.route("/links", methods=['GET', 'POST'])
def links():
    if current_user.is_authenticated:
        db_sess = db_session.create_session()
        links = db_sess.query(Link).filter(Link.user_id == current_user.id)

        def transit(link):
            tmp = 0
            transitions = db_sess.query(Transition).filter(Transition.link_id == link.id)
            for transit in transitions:
                tmp += 1
            return tmp

        return render_template("links.html", title="Cсылки", links=links, transit=transit)
    return redirect('/login')


@app.route('/link_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def link_delete(id):
    db_sess = db_session.create_session()
    link = db_sess.query(Link).filter(Link.id == id,
                                      Link.user == current_user
                                      ).first()
    if link:
        db_sess.delete(link)
        db_sess.commit()
    else:
        abort(404)
    return redirect('/links')


@app.route('/statistics_link/<int:id>', methods=['GET', 'POST'])
@login_required
def link_statistics(id):
    db_sess = db_session.create_session()
    links = db_sess.query(Link).filter(Link.user_id == current_user.id, Link.id == id)
    day = 0
    month = 0
    _all = 0
    for link in links:
        transitions = db_sess.query(Transition).filter(Transition.link_id == link.id)
        for transit in transitions:
            _all += 1
        transitions = db_sess.query(Transition).filter(Transition.link_id == link.id).filter(
            Transition.created_date > datetime.datetime.now() - datetime.timedelta(days=1))
        for transit in transitions:
            day += 1
        transitions = db_sess.query(Transition).filter(Transition.link_id == link.id).filter(
            Transition.created_date > datetime.datetime.now() - datetime.timedelta(weeks=4))
        for transit in transitions:
            month += 1
    return render_template("statistics.html", title="Cтатистика", day=day, month=month, all=_all)


@app.route("/api-doc", methods=['GET', 'POST'])
def api_doc():
    if current_user.is_authenticated:
        api_token = current_user.apikey

        return render_template("api-doc.html", title="API", api_token=api_token)
    return redirect('/login')


@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация', form=form,
                                   message="Пароли не совпадают!")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация', form=form,
                                   message="Такой пользователь уже есть!")
        user = User(
            name=form.name.data,
            email=form.email.data,
        )
        user.apikey = generate_alphanum_crypt_string(32)
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        links = db_sess.query(Link).filter(Link.user_id == session.get('temp_id', -1))
        for link in links:
            link.user_id = user.id
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            links = db_sess.query(Link).filter(Link.user_id == session.get('temp_id', -1))
            for link in links:
                link.user_id = user.id
            db_sess.commit()
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


def main():
    db_session.global_init("db/DateBase.db")
    api.add_resource(links_resourse.LinksResource, '/api/v1/links/<links_alias>')
    api.add_resource(links_resourse.LinksListResource, '/api/v1/links')
    app.run(host='0.0.0.0', port=3000)


if __name__ == '__main__':
    main()
