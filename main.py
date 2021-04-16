import datetime
import sqlite3
import vk_api
from flask import Flask, render_template, redirect, request
from flask import abort
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from flask_ngrok import run_with_ngrok
from data import db_session, users, accounts
from data.news import News
from data.users import User, LoginForm
from forms.news import NewsForm
from forms.user import RegisterForm
from forms.edit import RedactMailForm, RedactNameForm, RedactPasswordForm, MarketForm

app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)
run_with_ngrok(app)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
UPLOAD_STATIC = 'static/img/user_avatars/'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_STATIC'] = UPLOAD_STATIC
edit_mode = False
ADMINS = [1, 2]
GROUP_TOKEN = '362ed726c14963a17c777db697e93fb0c371c60' \
              '71bd08be014138bfdef0bbcbbe2755016e25bda6143739'


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
                               photo=current_user.photo, is_photo=current_user.is_photo)
    return render_template('startpage.html', title='Главная')


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
                                   message="Введите пароль от 8 символов")
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
                                   message="Данное имя пользователя занято")
        if len(form.name.data) <= 4:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Слишком короткое имя пользователя")
        user = users.User(
            name=form.name.data,
            email=form.email.data,
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


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        session = db_session.create_session()
        try:
            photo = request.files['file']
            name = app.config['UPLOAD_STATIC'] + photo.filename
            photo.save(name)
        except Exception:
            pass
        if str(photo) != "<FileStorage: '' ('application/octet-stream')>":
            user = session.query(User).filter(User.id == current_user.id).first()
            user.photo = name
            user.is_photo = True
            session.commit()
            return redirect('/profile')
    return render_template('profile.html', name=current_user.name,
                           photo=current_user.photo, email=current_user.email,
                           created_date=str(current_user.created_date).split()[0].split('-'),
                           title=current_user.name, is_photo=current_user.is_photo)


@app.route('/redact_mail', methods=['GET', 'POST'])
@login_required
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
                           photo=current_user.photo, is_photo=current_user.is_photo)


@app.route('/redact_password', methods=['GET', 'POST'])
@login_required
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
                                   message="Введите пароль от 8 символов")
        if form.password_old.data == form.password_new.data:
            return render_template('redact_password.html', title='Смена пароля',
                                   form=form,
                                   message="Вы ввели одинаковые пароли")
        for user in session.query(User).filter(User.id == current_user.id):
            user.set_password(form.password_new.data)
            session.commit()
        return redirect('/profile')
    return render_template('redact_password.html', title='Смена пароля', form=form,
                           photo=current_user.photo, is_photo=current_user.is_photo)


@app.route('/redact_name', methods=['GET', 'POST'])
@login_required
def redact_name():
    form = RedactNameForm()
    if form.validate_on_submit():
        session = db_session.create_session()
        if session.query(users.User).filter(
                users.User.name == form.name_new.data).first():
            return render_template('redact_name.html', title='Редактирование имени пользователя',
                                   form=form,
                                   message="Данное имя пользователя занято")
        if len(form.name_new.data) <= 4:
            return render_template('redact_name.html', title='Редактирование имени пользователя',
                                   form=form,
                                   message="Слишком короткое имя пользователя")
        for user in session.query(User).filter(User.id == current_user.id):
            user.name = form.name_new.data
            session.commit()
        return redirect('/profile')
    return render_template('redact_name.html', title='Редактирование имени пользователя',
                           form=form, photo=current_user.photo, is_photo=current_user.is_photo)


@app.route('/news', methods=['GET', 'POST'])
def news():
    global edit_mode
    db_sess = db_session.create_session()
    news = db_sess.query(News)
    arr = []
    for item in news:
        delta = datetime.datetime.now() - item.created_date
        if delta.days != 0:
            arr.append([item.title, item.content, delta.days, 'days', item.id])
        elif int(str(delta).split()[0].split(':')[0]) != 0:
            arr.append(
                [item.title, item.content, int(str(delta).split()[0].split(':')[0]), 'hours',
                 item.id])
        else:
            arr.append([item.title, item.content,
                        int(str(delta).split()[0].split(':')[1]), 'minutes', item.id])
        if current_user.is_authenticated:
            return render_template('news.html', title='Новости', news=arr[::-1],
                                   photo=current_user.photo, edit_mode=edit_mode, ADMINS=ADMINS)
    return render_template('news.html', title='Новости', news=arr[::-1],
                           ADMINS=ADMINS)


@app.route('/news_edit')
@login_required
def news_edit_mode():
    if current_user.id in ADMINS:
        global edit_mode
        edit_mode = not edit_mode
        return redirect('/news')
    return render_template('no_perm.html', title='Ошибка', is_photo=current_user.is_photo,
                           photo=current_user.photo)


@app.route('/delete', methods=['GET', 'POST'])
@login_required
def delete():
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id == current_user.id).first()
    db_sess.delete(user)
    db_sess.commit()
    return redirect('/')


@app.route('/delete_avatar', methods=['GET', 'POST'])
@login_required
def delete_avatar():
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id == current_user.id).first()
    user.is_photo = False
    user.photo = '-'
    db_sess.commit()
    return redirect('/profile')


@app.route('/delete_news/<int:id>')
@login_required
def delete_news(id):
    if current_user.id in ADMINS:
        db_sess = db_session.create_session()
        news = db_sess.query(News).filter(News.id == id).first()
        db_sess.delete(news)
        db_sess.commit()
        return redirect('/news')
    return render_template('no_perm.html', title='Ошибка', is_photo=current_user.is_photo,
                           photo=current_user.photo)


@app.route('/add_news', methods=['GET', 'POST'])
@login_required
def add_news():
    if current_user.id in ADMINS:
        form = NewsForm()
        if form.validate_on_submit():
            db_sess = db_session.create_session()
            news = News()
            news.title = form.title.data
            news.content = form.content.data
            news.created_date = datetime.datetime.now()
            current_user.news.append(news)
            db_sess.merge(current_user)
            db_sess.commit()
            return redirect('/news')
        return render_template('add_news.html', title='Добавление новости',
                               form=form, photo=current_user.photo, is_photo=current_user.is_photo)
    return render_template('no_perm.html', title='Ошибка', is_photo=current_user.is_photo,
                           photo=current_user.photo)


@app.route('/edit_news/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_news(id):
    if current_user.id in ADMINS:
        form = NewsForm()
        if request.method == "GET":
            db_sess = db_session.create_session()
            news = db_sess.query(News).filter(News.id == id,
                                              News.user == current_user
                                              ).first()
            if news:
                form.title.data = news.title
                form.content.data = news.content
            else:
                abort(404)
        if form.validate_on_submit():
            db_sess = db_session.create_session()
            news = db_sess.query(News).filter(News.id == id,
                                              News.user == current_user
                                              ).first()
            if news:
                news.title = form.title.data
                news.content = form.content.data
                news.created_date = datetime.datetime.now()
                db_sess.commit()
                return redirect('/')
            else:
                abort(404)
        return render_template('add_news.html',
                               title='Редактирование новости',
                               form=form, photo=current_user.photo, edit=True)
    return render_template('no_perm.html', title='Ошибка', is_photo=current_user.is_photo,
                           photo=current_user.photo)


@app.route('/contacts')
def contacts():
    ymap = "static/img/map_photo.png"
    return render_template('contacts.html', filename=ymap, photo=current_user.photo,
                           title='Контакты', is_photo=current_user.is_photo)


@app.route('/improvements')
@login_required
def impr():
    if current_user.id in ADMINS:
        con = sqlite3.connect('db/vkbot.db')
        cur = con.cursor()
        vk_group_session = vk_api.VkApi(token=GROUP_TOKEN)
        data = cur.execute('SELECT * FROM improvements').fetchall()
        arr = []
        for item in data:
            delta = datetime.datetime.now() - datetime.datetime.strptime(item[2],
                                                                         '%Y-%m-%d %H:%M:%S')
            user = \
            vk_group_session.method("users.get", {"user_ids": item[0], "fields": "photo_50"})[0]
            if delta.days != 0:
                arr.append(
                    [[user['first_name'], user['last_name'], item[0], user['photo_50']], item[1],
                     delta.days, 'days'])
            elif int(str(delta).split()[0].split(':')[0]) != 0:
                arr.append(
                    [[user['first_name'], user['last_name'], item[0], user['photo_50']], item[1],
                     int(str(delta).split(':')[0]), 'hours'])
            else:
                arr.append(
                    [[user['first_name'], user['last_name'], item[0], user['photo_50']], item[1],
                     int(str(delta).split(':')[1]), 'minutes'])
        return render_template('reviews.html', title='Отзывы', reviews=arr[::-1],
                               is_photo=current_user.is_photo,
                               photo=current_user.photo, impr=True)
    return render_template('no_perm.html', title='Ошибка', is_photo=current_user.is_photo,
                           photo=current_user.photo)


@app.route('/reviews')
def reviews():
    con = sqlite3.connect('db/vkbot.db')
    cur = con.cursor()
    vk_group_session = vk_api.VkApi(token=GROUP_TOKEN)
    data = cur.execute('SELECT * FROM reviews').fetchall()
    arr = []
    for item in data:
        delta = datetime.datetime.now() - datetime.datetime.strptime(item[2], '%Y-%m-%d %H:%M:%S')
        user = vk_group_session.method("users.get", {"user_ids": item[0], "fields": "photo_50"})[0]
        if delta.days != 0:
            arr.append(
                [[user['first_name'], user['last_name'], item[0], user['photo_50']], item[1],
                 delta.days, 'days'])
        elif int(str(delta).split()[0].split(':')[0]) != 0:
            arr.append(
                [[user['first_name'], user['last_name'], item[0], user['photo_50']], item[1],
                 int(str(delta).split(':')[0]), 'hours'])
        else:
            arr.append(
                [[user['first_name'], user['last_name'], item[0], user['photo_50']], item[1],
                 int(str(delta).split(':')[1]), 'minutes'])
    return render_template('reviews.html', title='Отзывы', reviews=arr,
                           is_photo=current_user.is_photo,
                           photo=current_user.photo, ADMINS=ADMINS)


@app.route('/market', methods=['POST', 'GET'])
def market():
    session = db_session.create_session()
    account_session = session.query(accounts.Accounts).all()
    account_dict = {}
    for account in account_session[::-1]:
        account_dict[account.title] = [account.price, account.count, account.link,
                                       account.user_name, account.type, account.id,
                                       account.created_date, account.about_acc]
    if current_user.is_authenticated:
        return render_template('market.html', name=current_user.name,
                               photo=current_user.photo, account_dict=account_dict)
    return render_template('market.html', account_dict=account_dict)


@login_required
@app.route('/add_acc', methods=['POST', 'GET'])
def add_item():
    form = MarketForm()
    if form.validate_on_submit():
        session = db_session.create_session()
        acc = accounts.Accounts()
        if len(form.name.data) <= 5:
            return render_template('add_acc.html', form=form,
                                   name=current_user.name, photo=current_user.photo,
                                   message='Вы ввели слишком короткое название аккаунта.'
                                           'Введите название от 5 символов')
        acc.title = form.name.data
        acc.type = form.category.data
        acc.link = form.link.data
        acc.price = form.price.data
        acc.count = form.count.data
        acc.user_name = current_user.name
        acc.about_acc = form.about.data
        session.add(acc)
        session.commit()
        account_session = session.query(accounts.Accounts).all()
        account_dict = {}
        for account in account_session:
            account_dict[account.title] = [account.price, account.count, account.link,
                                           account.user_name, account.type, account.id,
                                           account.created_date, account.about_acc]
        return redirect('/market')
    return render_template('add_acc.html',
                           name=current_user.name,
                           photo=current_user.photo, form=form)


@app.route('/edit_acc/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_item(id):
    form = MarketForm()
    if request.method == 'GET':
        session = db_session.create_session()
        account_session =\
            session.query(accounts.Accounts).filter(accounts.Accounts.id == id).first()
        if account_session:
            form.name.data = account_session.title
            form.category.data = account_session.type
            form.link.data = account_session.link
            form.price.data = account_session.price
            form.count.data = account_session.count
            form.about.data = account_session.about_acc
        else:
            abort(404)
    if form.validate_on_submit():
        session = db_session.create_session()
        account_session = session.query(accounts.Accounts).filter(accounts.Accounts.id == id).first()
        if account_session:
            account_session.title = form.name.data
            account_session.type = form.category.data
            account_session.link = form.link.data
            account_session.price = form.price.data
            account_session.count = form.count.data
            account_session.about_acc = form.about.data
            session.commit()
            return redirect('/market')
        else:
            abort(404)
    return render_template('add_acc.html', form=form,
                           name=current_user.name, photo=current_user.photo)


@app.route('/delete_acc/<int:id>', methods=['GET', 'POST'])
@login_required
def item_delete(id):
    session = db_session.create_session()
    account_session = session.query(accounts.Accounts).filter(accounts.Accounts.id == id).first()
    if account_session:
        session.delete(account_session)
        session.commit()
    else:
        abort(404)
    return redirect('/market')


@app.route('/market/<category>', methods=['POST', 'GET'])   
def sorted_market(category):
    session = db_session.create_session()
    if category == 'vk':
        account_session = session.query(accounts.Accounts).filter(accounts.Accounts.type
                                                                  == 'VK')
    elif category == 'steam':
        account_session = session.query(accounts.Accounts).filter(accounts.Accounts.type
                                                                  == 'Steam')
    elif category == 'instagram':
        account_session = session.query(accounts.Accounts).filter(accounts.Accounts.type
                                                                  == 'Instagram')
    elif category == 'origin':
        account_session = session.query(accounts.Accounts).filter(accounts.Accounts.type
                                                                  == 'Origin')
    elif category == 'mail':
        account_session = session.query(accounts.Accounts).filter(accounts.Accounts.type
                                                                  == 'Mail')
    else:
        account_session = session.query(accounts.Accounts).filter(accounts.Accounts.type
                                                                  == 'Other')
    account_dict = {}
    for account in account_session[::-1]:
        account_dict[account.title] = [account.price, account.count, account.link,
                                       account.user_name, account.type, account.id,
                                       account.created_date, account.about_acc]
    if current_user.is_authenticated:
        return render_template('market.html',
                               name=current_user.name,
                               photo=current_user.photo, account_dict=account_dict)
    return render_template('market.html', account_dict=account_dict)


if __name__ == '__main__':
    db_session.global_init("db/logins.db")
    app.run()
