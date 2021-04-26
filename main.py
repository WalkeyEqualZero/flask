from flask import Flask, render_template, redirect, make_response, request, session, abort, send_file
from login_form import LoginForm, FlaskForm, BooleanField
from data import db_session
from data.users import User
from data.news import News
from data.hubs import Hubs
from forms.hubs import HubsForm
import datetime
from forms.user import RegisterForm, EmailField, PasswordField, DataRequired, SubmitField
from forms.news import NewsForm
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(
    days=365
)
login_manager = LoginManager()
login_manager.init_app(app)


class LoginForm(FlaskForm):
    email = EmailField('Почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


@app.route('/')
@app.route('/index')
def index():
    db_sess = db_session.create_session()
    news = db_sess.query(Hubs)
    if current_user.is_authenticated:
        string = ''
        hubs = eval(current_user.user_hubs)
        if hubs != []:
            for i in range(len(hubs)):
                string += f'(Hubs.id == {hubs[i]}) | '
            news = news.filter(eval(string[:-2]))
            print(news)
        else:
            news = news.filter((Hubs.id == 1), (Hubs.id == 2))
    else:
        return render_template("unauthorized.html", news=news)
    return render_template("index.html", news=news)


@app.route('/hub/<int:id>')
@login_required
def hub(id):
    db_sess = db_session.create_session()
    the_hub = db_sess.query(Hubs).filter_by(id=id).first()
    if the_hub:
        admin = db_sess.query(Hubs).filter_by(id=id).first().admin
        if current_user.is_authenticated and id in eval(current_user.user_hubs) and current_user.id != admin:
            news = db_sess.query(News).filter(
                (News.id_user == current_user.id), (News.hub_id == id))
        elif current_user.is_authenticated and id in eval(current_user.user_hubs) and current_user.id == admin:
            news = db_sess.query(News).filter((News.hub_id == id))
        else:
            hub_name = db_sess.query(Hubs).filter_by(id=id).first().name
            return render_template("request.html", hub_name=hub_name, id_hub=id)
        return render_template("hub.html", news=news, id_hub=id, admin_id=admin)
    else:
        abort(404)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        if db_sess.query(User).filter(User.tg == form.tg.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Данный телеграм уже используется")
        user = User(
            name=form.name.data,
            email=form.email.data,
            about=form.about.data,
            tg=form.tg.data
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route('/quest/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_quest(id):
    form = NewsForm()
    if request.method == "GET":
        db_sess = db_session.create_session()
        hub_id_news = db_sess.query(News).filter_by(id=id).first().hub_id
        news = db_sess.query(News).filter(News.id == id,
                                          ).first()
        if db_sess.query(Hubs).filter_by(id=hub_id_news).first().admin == current_user.id:
            form.title.data = news.title
            form.content.data = news.content
            form.id_user.data = news.id_user
        else:
            abort(404)
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        hub_id_news = db_sess.query(News).filter_by(id=id).first().hub_id
        news = db_sess.query(News).filter(News.id == id,
                                          ).first()
        if db_sess.query(Hubs).filter_by(id=hub_id_news).first().admin == current_user.id:
            news.title = form.title.data
            news.content = form.content.data
            news.id_user = form.id_user.data
            db_sess.commit()
            return redirect(f'/hub/{hub_id_news}')
        else:
            abort(404)
    return render_template('news.html',
                           title='Редактирование задания',
                           form=form
                           )


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route('/hub/<int:id>/quest',  methods=['GET', 'POST'])
@login_required
def add_quest(id):
    form = NewsForm()
    db_sess = db_session.create_session()
    if db_sess.query(Hubs).filter_by(id=id).first().admin == current_user.id:
        if form.validate_on_submit():
            news = News()
            news.title = form.title.data
            news.content = form.content.data
            news.hub_id = id
            news.id_user = form.id_user.data
            current_user.news.append(news)
            db_sess.merge(current_user)
            db_sess.commit()
            return redirect(f'/hub/{id}')
        return render_template('news.html', title='Добавление новости',
                               form=form)
    else:
        abort(404)


@app.route('/quest_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def news_delete(id):
    db_sess = db_session.create_session()
    news = db_sess.query(News).filter(News.id == id,
                                      News.user == current_user
                                      ).first()
    hub_id_news = db_sess.query(News).filter_by(id=id).first().hub_id
    if news:
        db_sess.delete(news)
        db_sess.commit()
    else:
        abort(404)
    return redirect(f'/hub/{hub_id_news}')


@app.route('/images/<name>')
def images(name):
    DIRECTORY_IMAGES = os.path.join(os.path.dirname(__file__), "templates/images")
    return send_file(os.path.join(DIRECTORY_IMAGES, name))


@app.route('/new_hub',  methods=['GET', 'POST'])
@login_required
def add_hub():
    form = HubsForm()
    db_sess = db_session.create_session()
    if current_user.is_authenticated:
        if form.validate_on_submit():
            hubs = Hubs()
            hubs.name = form.name.data
            hubs.admin = current_user.id
            user_hubs = list(map(str, eval(current_user.user_hubs)))
            current_user.hubs.append(hubs)
            db_sess.merge(current_user)
            db_sess.commit()
            news = db_sess.query(Hubs).filter(Hubs.admin == current_user.id)
            for el in news:
                if el.id not in user_hubs:
                    user_hubs.append(str(el.id))
            user = db_sess.query(User).filter(User.id == current_user.id).first()
            user.user_hubs = '[' + ', '.join(user_hubs) + ']'
            db_sess.commit()
            return redirect('/')
        return render_template('new_hub.html', title='Добавление новости',
                               form=form)
    else:
        abort(404)


@app.route('/hub_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def hub_delete(id):
    db_sess = db_session.create_session()
    news = db_sess.query(Hubs).filter(Hubs.id == id).first()
    if news and news.admin == current_user.id:
        db_sess.delete(news)
        db_sess.commit()
    else:
        abort(404)
    return redirect(f'/')


@app.route('/hub/<int:id>/request',  methods=['GET', 'POST'])
@login_required
def post_request(id):
    if id not in eval(current_user.user_hubs):
        db_sess = db_session.create_session()
        hub = db_sess.query(Hubs).filter(Hubs.id == id).first()
        hub_requests = list(map(str, eval(hub.requests)))
        hub_requests.append(str(current_user.id))
        hub.requests = '[' + ', '.join(hub_requests) + ']'
        print(hub_requests)
        db_sess.commit()
        return redirect('/')
    else:
        abort(404)


@app.route('/hub/<int:id>/admin', methods=['GET', 'POST'])
@login_required
def hub_admin(id):
    db_sess = db_session.create_session()
    if db_sess.query(Hubs).filter_by(id=id).first().admin == current_user.id:
        hub = db_sess.query(Hubs).filter(Hubs.id == id).first()
        users = db_sess.query(User)
        requests = list(map(str, eval(hub.requests)))
        string = ''
        if requests != []:
            for i in range(len(requests)):
                string += f'(User.id == {requests[i]}) | '
            print(string)
            users = users.filter(eval(string[:-2]))
        else:
            users = users.filter((Hubs.id == 1), (Hubs.id == 2))
        return render_template("requests.html", users=users, id=id)
    else:
        abort(405)


@app.route('/hub/<int:id>/decline/<int:user_id>',  methods=['GET', 'POST'])
@login_required
def delete_request(id, user_id):
    db_sess = db_session.create_session()
    if db_sess.query(Hubs).filter_by(id=id).first().admin == current_user.id:
        hub = db_sess.query(Hubs).filter(Hubs.id == id).first()
        hub_requests = list(map(str, eval(hub.requests)))
        hub_requests.remove(str(user_id))
        hub.requests = '[' + ', '.join(hub_requests) + ']'
        print(hub_requests)
        db_sess.commit()
        return redirect('/')
    else:
        abort(404)


@app.route('/hub/<int:id>/accept/<int:user_id>',  methods=['GET', 'POST'])
@login_required
def accept_request(id, user_id):
    db_sess = db_session.create_session()
    if db_sess.query(Hubs).filter_by(id=id).first().admin == current_user.id:
        hub = db_sess.query(Hubs).filter(Hubs.id == id).first()
        hub_requests = list(map(str, eval(hub.requests)))
        hub_requests.remove(str(user_id))
        hub.requests = '[' + ', '.join(hub_requests) + ']'
        print(hub_requests)
        user = db_sess.query(User).filter(User.id == user_id).first()
        user_hubs = list(map(str, eval(hub.requests)))
        user_hubs.append(str(id))
        user.user_hubs = '[' + ', '.join(user_hubs) + ']'
        db_sess.commit()
        return redirect('/')
    else:
        abort(404)


if __name__ == '__main__':
    db_session.global_init("db/blogs.db")
    db_sess = db_session.create_session()
    app.run(port=8080, host='127.0.0.1')
