from flask import Flask, render_template, redirect, request
from flask_ngrok import run_with_ngrok
from flask_wtf import FlaskForm
from wtforms import PasswordField, SubmitField, StringField
from wtforms.validators import DataRequired
from data import db_session, users
from data.users import User, LoginForm
from data.news import News
from forms.user import RegisterForm
from flask_login import LoginManager, login_user, logout_user, current_user, login_required

app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)
run_with_ngrok(app)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
UPLOAD_STATIC = 'static/img/'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_STATIC'] = UPLOAD_STATIC


class RedactMailForm(FlaskForm):
    email_new = StringField('Новая почта', validators=[DataRequired()])
    submit = SubmitField('Изменить данные')


class RedactPasswordForm(FlaskForm):
    password_old = PasswordField('Старый пароль', validators=[DataRequired()])
    password_new = PasswordField('Новый пароль', validators=[DataRequired()])
    submit = SubmitField('Изменить данные')


class RedactNameForm(FlaskForm):
    name_new = StringField('Новое имя пользователя', validators=[DataRequired()])
    submit = SubmitField('Изменить данные')


class LoadPhotoForm(FlaskForm):
    submit = SubmitField('Загрузить фотографию')


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route('/')
def index():
    if current_user.is_authenticated:
        return render_template('startpage.html', title='Главная',
                               photo=current_user.photo)
    return render_template('startpage.html', title='Главная')


@app.route('/terms')
def terms():
    if current_user.is_authenticated:
        return render_template('terms.html', title='Положения и гарантии',
                               photo=current_user.photo)
    return render_template('terms.html', title='Положения и гарантии')


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        if len(form.password.data) <= 8:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Вы ввели короткий пароль \n\n\n"
                                           "Введите пароль от 8 символов")
        session = db_session.create_session()
        if session.query(users.User).filter(
                users.User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Данная почта уже зарегистрирована")
        if session.query(users.User).filter(
                users.User.name == form.name.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пользователь с таким именем уже зарегистрирован")
        if len(form.name.data) <= 4:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Вы ввели короткое имя пользователя \n\n\n"
                                           "Введите имя от 4 символов")
        user = users.User(
            name=form.name.data,
            email=form.email.data,
            photo='/static/img/user_new.png'
        )
        user.set_password(form.password.data)
        session.add(user)
        session.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        session = db_session.create_session()
        user = session.query(users.User).filter(users.User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        elif user:
            return render_template('login.html',
                                   message="Неправильный логин или пароль",
                                   form=form)
        else:
            return render_template('login.html',
                                   message="Такого пользователя не существует",
                                   form=form)
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route('/profile')
def profile():
    return render_template('profile.html', name=current_user.name,
                           photo=current_user.photo, email=current_user.email,
                           created_date=str(current_user.created_date).split()[0].split('-'),
                           title=current_user.name)


@app.route('/redact_mail', methods=['GET', 'POST'])
def redact_mail():
    form = RedactMailForm()
    if form.validate_on_submit():
        session = db_session.create_session()
        if session.query(users.User).filter(
                users.User.email == form.email_new.data).first():
            return render_template('redact_mail.html', title='Редактирование почты',
                                   form=form,
                                   message="Данная почта уже зарегистрирована")
        for user in session.query(User).filter(User.id == current_user.id):
            user.email = form.email_new.data
            session.commit()
        return redirect('/profile')
    return render_template('redact_mail.html', title='Редактирование почты', form=form,
                           photo=current_user.photo)


@app.route('/redact_password', methods=['GET', 'POST'])
def redact_password():
    form = RedactPasswordForm()
    if form.validate_on_submit():
        session = db_session.create_session()
        if not current_user.check_password(form.password_old.data):
            return render_template('redact_password.html', title='Смена пароля',
                                   form=form,
                                   message="Вы ввели неверный пароль")
        if len(form.password_new.data) <= 8:
            return render_template('redact_password.html', title='Смена пароля',
                                   form=form,
                                   message="Вы ввели короткий пароль \n\n\n"
                                           "Введите пароль от 8 символов")
        if form.password_old.data == form.password_new.data:
            return render_template('redact_password.html', title='Смена пароля',
                                   form=form,
                                   message="Вы ввели одинаковые пароли")
        for user in session.query(User).filter(User.id == current_user.id):
            user.set_password(form.password_new.data)
            session.commit()
        return redirect('/profile')
    return render_template('redact_password.html', title='Смена пароля', form=form,
                           photo=current_user.photo)


@app.route('/redact_name', methods=['GET', 'POST'])
def redact_name():
    form = RedactNameForm()
    if form.validate_on_submit():
        session = db_session.create_session()
        if session.query(users.User).filter(
                users.User.name == form.name_new.data).first():
            return render_template('redact_name.html', title='Редактирование имени пользователя',
                                   form=form,
                                   message="Пользователь с таким именем уже зарегистрирован")
        if len(form.name_new.data) <= 4:
            return render_template('redact_name.html', title='Редактирование имени пользователя',
                                   form=form,
                                   message="Вы ввели короткое имя пользователя \n\n\n"
                                           "Введите имя от 4 символов")
        for user in session.query(User).filter(User.id == current_user.id):
            user.name = form.name_new.data
            session.commit()
        return redirect('/profile')
    return render_template('redact_name.html', title='Редактирование имени пользователя',
                           form=form, photo=current_user.photo)


@app.route('/load_photo', methods=['GET', 'POST'])
def load_photo():
    form = LoadPhotoForm()
    if form.validate_on_submit():
        session = db_session.create_session()
        try:
            photo = request.files['file']
            name = app.config['UPLOAD_STATIC'] + photo.filename
            photo.save(name)
        except Exception:
            pass
        for user in session.query(User).filter(User.id == current_user.id):
            user.photo = name
            session.commit()
        return redirect('/profile')
    return render_template('load_photo.html', title='Загрузка фотографии',
                           form=form, photo=current_user.photo)


@app.route('/news', methods=['GET', 'POST'])
def news():
    db_sess = db_session.create_session()
    news = db_sess.query(News)
    if current_user.is_authenticated:
        return render_template('news.html', title='Новости',
                               photo=current_user.photo, news=news)
    return render_template('news.html', title='Новости', news=news)


if __name__ == '__main__':
    db_session.global_init("db/logins.db")
    app.run()
