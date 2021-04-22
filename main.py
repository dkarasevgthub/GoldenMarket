import datetime
import os
import sqlite3
from PIL import Image

import vk_api
from flask import Flask, render_template, redirect, request, abort
from flask_login import LoginManager, login_user, logout_user, current_user, login_required

from data import db_session, users, accounts
from data.news import News
from data.users import User
from forms.edit import RedactMailForm, RedactNameForm, RedactPasswordForm, MarketForm
from forms.news import NewsForm
from forms.user import RegisterForm, LoginForm

app = Flask(__name__)  # создание приложения
login_manager = LoginManager()
login_manager.init_app(app)
app.config['SECRET_KEY'] = 'yandex_lyceum_secret_key'
UPLOAD_STATIC = 'static/img/user_avatars/'  # папка для сохранения фотографий пользователей
app.config['UPLOAD_STATIC'] = UPLOAD_STATIC
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(days=365)
edit_mode = False  # мод редактирования новостей
ADMINS = [1, 3]  # список айди админов
GROUP_TOKEN = '362ed726c14963a17c777db697e93fb0c371c60' \
              '71bd08be014138bfdef0bbcbbe2755016e25bda6143739'  # токен группы вк


@login_manager.user_loader  # функция загрузки пользователя
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route('/')  # главная страница
def index():
    if current_user.is_authenticated:
        return render_template('start.html', title='Главная',
                               photo='/'.join(current_user.photo.split('/')[1:]),
                               is_photo=current_user.is_photo)
    return render_template('start.html', title='Главная')


@app.route('/register', methods=['GET', 'POST'])  # страница регистрации
def register():
    form = RegisterForm()  # создание формы
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:  # проверка на совпадение паролей
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        if len(form.password.data) <= 8:  # проверка на длину пароля
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Введите пароль от 8 символов")
        session = db_session.create_session()
        if session.query(users.User).filter(
                users.User.email == form.email.data).first():  # проверка на почту
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Данная почта уже зарегистрирована")
        if session.query(users.User).filter(
                users.User.name == form.name.data).first():  # проверка на имя пользователя
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Данное имя пользователя занято")
        if len(form.name.data) <= 4:  # проверка на длину имени пользователя
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Слишком короткое имя пользователя")
        user = users.User(
            name=form.name.data,
            email=form.email.data,
        )
        user.set_password(form.password.data)
        session.add(user)  # добавление пользователя в базу данных
        session.commit()
        return redirect('/login')
    if current_user.is_authenticated:
        return redirect('/')
    return render_template('register.html', title='Регистрация', form=form)


@app.route('/login', methods=['GET', 'POST'])  # страница входа
def login():
    form = LoginForm()  # создание формы
    if form.validate_on_submit():
        session = db_session.create_session()
        user = session.query(users.User).filter(users.User.email == form.email.data).first()
        if user and user.check_password(form.password.data):  # если верный пароль, то входим
            login_user(user)
            return redirect("/")
        elif user:  # если неверный логин и/или пароль
            return render_template('login.html',
                                   message="Неправильный логин и/или пароль",
                                   form=form)
        else:  # если пользователя не существует
            return render_template('login.html',
                                   message="Такого пользователя не существует",
                                   form=form)
    if current_user.is_authenticated:
        return redirect('/')
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/logout')  # выход пользователя
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route('/profile', methods=['GET', 'POST'])  # страница профиля
@login_required
def profile():
    if request.method == 'POST':
        session = db_session.create_session()
        photo = request.files['file']
        name = app.config['UPLOAD_STATIC'] + photo.filename
        try:
            photo.save(name)
            img = Image.open(name)
            w, h = img.size
            if w > h:
                area = ((w - h) // 2, 0, h + (w - h) // 2, h)
            else:
                area = (0, (h - w) // 2, w, w + (h - w) // 2)
            cropped_img = img.crop(area)
            cropped_img.save(name)
        except Exception:
            return render_template('profile.html', name=current_user.name,
                                   photo='/'.join(current_user.photo.split('/')[1:]),
                                   email=current_user.email,
                                   created_date=str(current_user.created_date).split()[0].split(
                                       '-'),
                                   title=current_user.name, is_photo=current_user.is_photo,
                                   message='Вы не выбрали фотографию.')
        if str(photo) != "<FileStorage: '' ('application/octet-stream')>":  # присвоение фото user
            user = session.query(User).filter(User.id == current_user.id).first()
            user.photo = name
            user.is_photo = True
            session.commit()
            return redirect('/profile')
    return render_template('profile.html', name=current_user.name,
                           photo='/'.join(current_user.photo.split('/')[1:]),
                           email=current_user.email,
                           created_date=str(current_user.created_date).split()[0].split('-'),
                           title=current_user.name, is_photo=current_user.is_photo)


@app.route('/redact_mail', methods=['GET', 'POST'])  # страница редактирования почты
@login_required
def redact_mail():
    form = RedactMailForm()  # создание формы
    if form.validate_on_submit():
        session = db_session.create_session()
        if session.query(users.User).filter(
                users.User.email == form.email_new.data).first():  # зарегистрирована ли почта
            return render_template('redact_mail.html', title='Редактирование почты',
                                   form=form,
                                   message="Данная почта уже зарегистрирована",
                                   photo='/'.join(current_user.photo.split('/')[1:]),
                                   is_photo=current_user.is_photo)
        for user in session.query(User).filter(User.id == current_user.id):
            user.email = form.email_new.data
            session.commit()
        return redirect('/profile')
    return render_template('redact_mail.html', title='Редактирование почты', form=form,
                           photo='/'.join(current_user.photo.split('/')[1:]),
                           is_photo=current_user.is_photo)


@app.route('/redact_password', methods=['GET', 'POST'])  # форма редактирования пароля
@login_required
def redact_password():
    form = RedactPasswordForm()  # создание формы
    if form.validate_on_submit():
        session = db_session.create_session()
        if not current_user.check_password(form.password_old.data):  # если неверный пароль
            return render_template('redact_password.html', title='Смена пароля',
                                   form=form,
                                   message="Вы ввели неверный пароль",
                                   photo='/'.join(current_user.photo.split('/')[1:]),
                                   is_photo=current_user.is_photo)
        if len(form.password_new.data) <= 8:  # если короткий пароль
            return render_template('redact_password.html', title='Смена пароля',
                                   form=form,
                                   message="Введите пароль от 8 символов",
                                   photo='/'.join(current_user.photo.split('/')[1:]),
                                   is_photo=current_user.is_photo)
        if form.password_old.data == form.password_new.data:  # если старый == новый
            return render_template('redact_password.html', title='Смена пароля',
                                   form=form, photo='/'.join(current_user.photo.split('/')[1:]),
                                   is_photo=current_user.is_photo,
                                   message="Вы ввели одинаковые пароли")
        for user in session.query(User).filter(User.id == current_user.id):
            user.set_password(form.password_new.data)
            session.commit()
        return redirect('/profile')
    return render_template('redact_password.html', title='Смена пароля', form=form,
                           photo='/'.join(current_user.photo.split('/')[1:]),
                           is_photo=current_user.is_photo)


@app.route('/redact_name', methods=['GET', 'POST'])  # страница редактирования
@login_required
def redact_name():
    form = RedactNameForm()  # создание формы
    if form.validate_on_submit():
        session = db_session.create_session()
        if session.query(users.User).filter(
                users.User.name == form.name_new.data).first():  # если имя занято
            return render_template('redact_name.html', title='Редактирование имени пользователя',
                                   form=form, photo='/'.join(current_user.photo.split('/')[1:]),
                                   is_photo=current_user.is_photo,
                                   message="Данное имя пользователя занято")
        if len(form.name_new.data) <= 4:  # если имя короткое
            return render_template('redact_name.html', title='Редактирование имени пользователя',
                                   form=form, photo='/'.join(current_user.photo.split('/')[1:]),
                                   is_photo=current_user.is_photo,
                                   message="Слишком короткое имя пользователя")
        for user in session.query(User).filter(User.id == current_user.id):
            user.name = form.name_new.data
            session.commit()
        return redirect('/profile')
    return render_template('redact_name.html', title='Редактирование имени пользователя',
                           form=form, photo='/'.join(current_user.photo.split('/')[1:]),
                           is_photo=current_user.is_photo)


@app.route('/news', methods=['GET', 'POST'])  # страница новостей
def news():
    global edit_mode
    db_sess = db_session.create_session()
    all_news = db_sess.query(News)  # получение таблицы новостей из базы данных
    arr = []  # список для новостей
    for item in all_news:
        delta = datetime.datetime.now() - item.created_date
        if delta.days != 0:
            arr.append([item.title, item.content, delta.days, 'days', item.id])
        elif int(str(delta).split()[0].split(':')[0]) != 0:
            arr.append(
                [item.title, item.content, int(str(delta).split()[0].split(':')[0]), 'hours',
                 item.id])
        elif int(str(delta).split()[0].split(':')[1]) != 0:
            arr.append([item.title, item.content,
                        int(str(delta).split()[0].split(':')[1]), 'minutes', item.id])
        else:
            arr.append([item.title, item.content,
                        '', 'a few seconds', item.id])
    if current_user.is_authenticated:
        return render_template('news.html', title='Новости', news=arr[::-1],
                               photo='/'.join(current_user.photo.split('/')[1:]),
                               edit_mode=edit_mode,
                               ADMINS=ADMINS,
                               is_photo=current_user.is_photo)
    return render_template('news.html', title='Новости', news=arr[::-1])


@app.route('/news_edit')  # страница редактирования новостей
@login_required
def news_edit_mode():
    if current_user.id in ADMINS:  # проверка, является ли пользователь администратором
        global edit_mode
        edit_mode = not edit_mode
        return redirect('/news')
    return render_template('no_perm.html', title='Ошибка', is_photo=current_user.is_photo,
                           photo='/'.join(current_user.photo.split('/')[1:]))


@app.route('/delete', methods=['GET', 'POST'])  # удаление пользователя
@login_required
def delete():
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id == current_user.id).first()
    db_sess.delete(user)
    db_sess.commit()
    return redirect('/')


@app.route('/delete_avatar', methods=['GET', 'POST'])  # удаление фотографии пользователя
@login_required
def delete_avatar():
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id == current_user.id).first()
    user.is_photo = False
    user.photo = '-'
    db_sess.commit()
    return redirect('/profile')


@app.route('/delete_news/<int:delete_id>')  # удаление новости по id
@login_required
def delete_news(delete_id):
    if current_user.id in ADMINS:
        db_sess = db_session.create_session()
        news_delete = db_sess.query(News).filter(News.id == delete_id).first()
        db_sess.delete(news_delete)
        db_sess.commit()
        return redirect('/news')
    return render_template('no_perm.html', title='Ошибка', is_photo=current_user.is_photo,
                           photo='/'.join(current_user.photo.split('/')[1:]))


@app.route('/add_news', methods=['GET', 'POST'])  # добавление новости
@login_required
def add_news():
    if current_user.id in ADMINS:
        form = NewsForm()
        if form.validate_on_submit():
            db_sess = db_session.create_session()
            new_news = News()  # создание новости
            new_news.title = form.title.data
            new_news.content = form.content.data
            new_news.created_date = datetime.datetime.now()
            current_user.news.append(new_news)
            db_sess.merge(current_user)
            db_sess.commit()
            return redirect('/news')
        return render_template('add_news.html', title='Добавление новости',
                               form=form, photo='/'.join(current_user.photo.split('/')[1:]),
                               is_photo=current_user.is_photo)
    return render_template('no_perm.html', title='Ошибка', is_photo=current_user.is_photo,
                           photo='/'.join(current_user.photo.split('/')[1:]))


@app.route('/edit_news/<int:edit_id>', methods=['GET', 'POST'])  # редактирование новости по id
@login_required
def edit_news(edit_id):
    if current_user.id in ADMINS:  # проверка, является ли пользователь администратором
        form = NewsForm()
        if request.method == "GET":
            db_sess = db_session.create_session()
            news_edit = db_sess.query(News).filter(News.id == edit_id,
                                                   News.user == current_user).first()
            if news_edit:  # если новость существует, отображаем ее данные в форме
                form.title.data = news_edit.title
                form.content.data = news_edit.content
            else:
                abort(404)  # если новости не существует, выбрасываем ошибку 404
        if form.validate_on_submit():
            db_sess = db_session.create_session()
            news_edit = db_sess.query(News).filter(News.id == edit_id,
                                                   News.user == current_user
                                                   ).first()
            if news_edit:  # если новость существует, редактируем её
                news_edit.title = form.title.data
                news_edit.content = form.content.data
                news_edit.created_date = datetime.datetime.now()
                db_sess.commit()
                return redirect('/news')
            else:  # если новости не существует, выбрасываем ошибку 404
                abort(404)
        return render_template('add_news.html',
                               title='Редактирование новости',
                               form=form, photo=current_user.photo, edit=True)
    return render_template('no_perm.html', title='Ошибка', is_photo=current_user.is_photo,
                           photo='/'.join(current_user.photo.split('/')[1:]))


@app.route('/contacts')  # страница контактов
def contacts():
    map_pic = "static/img/map_photo.png"  # яндекс карта
    if current_user.is_authenticated:
        return render_template('contacts.html', filename=map_pic,
                               photo='/'.join(current_user.photo.split('/')[1:]),
                               title='Контакты', is_photo=current_user.is_photo)
    return render_template('contacts.html', filename=map_pic, title='Контакты')


@app.route('/improvements')  # предложения пользователей (видят только администраторы)
@login_required
def improvements():
    if current_user.id in ADMINS:  # является ли пользователь администратором
        con = sqlite3.connect('db/vk_bot.db')  # подключение базы данных вк-бота
        cur = con.cursor()
        vk_group_session = vk_api.VkApi(token=GROUP_TOKEN)
        data = cur.execute('SELECT * FROM improvements').fetchall()
        arr = []  # список пользователей
        for item in data:
            delta = datetime.datetime.now() - datetime.datetime.strptime(item[2],
                                                                         '%Y-%m-%d %H:%M:%S')
            user = \
                vk_group_session.method("users.get", {"user_ids": item[0], "fields": "photo_50"})[
                    0]
            if delta.days != 0:
                arr.append(
                    [[user['first_name'], user['last_name'], item[0], user['photo_50']], item[1],
                     delta.days, 'days'])
            elif int(str(delta).split()[0].split(':')[0]) != 0:
                arr.append(
                    [[user['first_name'], user['last_name'], item[0], user['photo_50']], item[1],
                     int(str(delta).split(':')[0]), 'hours'])
            elif int(str(delta).split(':')[1]) != 0:
                arr.append(
                    [[user['first_name'], user['last_name'], item[0], user['photo_50']], item[1],
                     int(str(delta).split(':')[1]), 'minutes'])
            else:
                arr.append(
                    [[user['first_name'], user['last_name'], item[0], user['photo_50']], item[1],
                     '', 'a few seconds'])
        return render_template('reviews.html', title='Предложения', reviews=arr[::-1],
                               is_photo=current_user.is_photo,
                               photo='/'.join(current_user.photo.split('/')[1:]), impr=True)
    return render_template('no_perm.html', title='Ошибка', is_photo=current_user.is_photo,
                           photo='/'.join(current_user.photo.split('/')[1:]))


@app.route('/reviews')  # страница отзывов пользователей
def reviews():
    con = sqlite3.connect('db/vk_bot.db')  # подключение базы данных вк-бота
    cur = con.cursor()
    vk_group_session = vk_api.VkApi(token=GROUP_TOKEN)
    data = cur.execute('SELECT * FROM reviews').fetchall()
    arr = []  # список пользователей
    for item in data[::-1]:
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
        elif int(str(delta).split(':')[1]) != 0:
            arr.append(
                [[user['first_name'], user['last_name'], item[0], user['photo_50']], item[1],
                 int(str(delta).split(':')[1]), 'minutes'])
        else:
            arr.append(
                [[user['first_name'], user['last_name'], item[0], user['photo_50']], item[1],
                 '', 'a few seconds'])
    if current_user.is_authenticated:
        return render_template('reviews.html', title='Отзывы', reviews=arr,
                               is_photo=current_user.is_photo,
                               photo='/'.join(current_user.photo.split('/')[1:]), ADMINS=ADMINS)
    return render_template('reviews.html', title='Отзывы', reviews=arr)


@app.route('/market', methods=['POST', 'GET'])  # страница маркета
def market():
    session = db_session.create_session()
    account_session = session.query(accounts.Accounts).all()
    account_dict = {}  # словарь аккаунтов
    for account in account_session[::-1]:
        account_dict[account.title] = [account.price, 1, account.link,
                                       account.user_name, account.type.lower(), account.id,
                                       str(account.created_date).split()[0].split('-'),
                                       account.about_acc,
                                       str(account.created_date).split()[1].split('.')[0].split(
                                           ':')]
    if current_user.is_authenticated:
        return render_template('market.html', name=current_user.name,
                               photo='/'.join(current_user.photo.split('/')[1:]),
                               account_dict=account_dict,
                               is_photo=current_user.is_photo, title='Аккануты', ADMINS=ADMINS)
    return render_template('market.html', account_dict=account_dict, title='Аккануты')


@app.route('/add_acc', methods=['POST', 'GET'])  # страница добавления аккаунта
@login_required
def add_item():
    form = MarketForm()  # создание формы
    if form.validate_on_submit():
        session = db_session.create_session()
        acc = accounts.Accounts()
        acc.title = form.name.data
        if len(acc.title) <= 5:  # если название аккаунта короче 5 символов
            return render_template('add_acc.html', form=form,
                                   name=current_user.name,
                                   photo='/'.join(current_user.photo.split('/')[1:]),
                                   is_photo=current_user.is_photo,
                                   message='Вы ввели слишком короткое название аккаунта.'
                                           'Введите название от 5 символов')
        acc.type = form.category.data
        acc.link = form.link.data
        if 'https://' not in acc.link:  # если в ссылке нет протокола https
            return render_template('add_acc.html', form=form,
                                   name=current_user.name,
                                   photo='/'.join(current_user.photo.split('/')[1:]),
                                   is_photo=current_user.is_photo,
                                   message='Вы ввели ссылку без протокола "https://"')
        acc.price = form.price.data
        if len(acc.price) > 6:  # если пользователь ввел слишком большую цену
            return render_template('add_acc.html', form=form,
                                   name=current_user.name,
                                   photo='/'.join(current_user.photo.split('/')[1:]),
                                   is_photo=current_user.is_photo,
                                   message='Вы слишком высокую цену на аккаунт. Снизьте цену')
        elif len(acc.price) == 0:  # если пользователь не ввел цену
            return render_template('add_acc.html', form=form,
                                   name=current_user.name,
                                   photo='/'.join(current_user.photo.split('/')[1:]),
                                   is_photo=current_user.is_photo,
                                   message='Вы не ввели цену аккаунта')
        acc.user_name = current_user.name
        acc.about_acc = form.about.data
        if len(acc.about_acc) < 15:  # если пользователь описал аккаунт слишком коротко
            return render_template('add_acc.html', form=form,
                                   name=current_user.name,
                                   photo='/'.join(current_user.photo.split('/')[1:]),
                                   is_photo=current_user.is_photo,
                                   message='Опишите ваш аккаунт более подробно')
        acc.user_id = current_user.id
        session.add(acc)
        session.commit()
        account_session = session.query(accounts.Accounts).all()
        account_dict = {}  # словарь аккаунтов
        for account in account_session:
            account_dict[account.title] = [account.price, 1, account.link,
                                           account.user_name, account.type, account.id,
                                           account.created_date, account.about_acc]
        return redirect('/market')
    return render_template('add_acc.html',
                           name=current_user.name,
                           photo='/'.join(current_user.photo.split('/')[1:]), form=form,
                           is_photo=current_user.is_photo, title='Продать аккаунт')


# страница редактирования аккаунтов
@app.route('/edit_acc/<int:edit_acc_id>', methods=['GET', 'POST'])
@login_required
def edit_item(edit_acc_id):
    form = MarketForm()  # создание формы
    if request.method == 'GET':
        session = db_session.create_session()
        account_session = \
            session.query(accounts.Accounts).filter(accounts.Accounts.id == edit_acc_id).first()
        if account_session:  # если аккаунт существует, отображаем его данные в форме
            form.name.data = account_session.title
            form.category.data = account_session.type
            form.link.data = account_session.link
            form.price.data = account_session.price
            form.about.data = account_session.about_acc
        else:  # если аккаунт не существует, выбрасываем ошибку 404
            abort(404)
    if form.validate_on_submit():
        session = db_session.create_session()
        account_session = session.query(accounts.Accounts).filter(
            accounts.Accounts.id == edit_acc_id).first()
        if account_session:
            account_session.title = form.name.data
            if len(account_session.title) <= 5:  # если название аккаунта короче 5 символов
                return render_template('add_acc.html', form=form,
                                       name=current_user.name,
                                       photo='/'.join(current_user.photo.split('/')[1:]),
                                       is_photo=current_user.is_photo,
                                       message='Вы ввели слишком короткое название аккаунта.'
                                               'Введите название от 5 символов')
            account_session.type = form.category.data
            account_session.link = form.link.data
            if 'https://' not in account_session.link:  # если в аккаунте нет протокола https
                return render_template('add_acc.html', form=form,
                                       name=current_user.name,
                                       photo='/'.join(current_user.photo.split('/')[1:]),
                                       is_photo=current_user.is_photo,
                                       message='Вы ввели ссылку без протокола "https://"')
            account_session.price = form.price.data
            if len(account_session.price) > 6:  # если пользователь ввел слишком большую цену
                return render_template('add_acc.html', form=form,
                                       name=current_user.name,
                                       photo='/'.join(current_user.photo.split('/')[1:]),
                                       is_photo=current_user.is_photo,
                                       message='Вы слишком высокую цену на аккаунт. Снизьте цену')
            elif len(account_session.price) == 0:  # если пользователь не ввел цену
                return render_template('add_acc.html', form=form,
                                       name=current_user.name,
                                       photo='/'.join(current_user.photo.split('/')[1:]),
                                       is_photo=current_user.is_photo,
                                       message='Вы не ввели цену аккаунта')
            account_session.about_acc = form.about.data
            if len(account_session.about_acc) < 15:  # если описали аккаунт слишком коротко
                return render_template('add_acc.html', form=form,
                                       name=current_user.name,
                                       photo='/'.join(current_user.photo.split('/')[1:]),
                                       is_photo=current_user.is_photo,
                                       message='Опишите ваш аккаунт более подробно')
            session.commit()
            return redirect('/market')
        else:  # если аккаунта не существует, выбрасываем ошибку 404
            abort(404)
    return render_template('add_acc.html', form=form,
                           name=current_user.name,
                           photo='/'.join(current_user.photo.split('/')[1:]),
                           is_photo=current_user.is_photo, title='Редактирование товара',
                           edit=True)


@app.route('/delete_acc/<int:acc_id>', methods=['GET', 'POST'])  # форма удаления аккаунта
@login_required
def item_delete(acc_id):
    session = db_session.create_session()
    account_session = session.query(accounts.Accounts).filter(
        accounts.Accounts.id == acc_id).first()
    if account_session:  # если аккаунт существует, удаляем его
        session.delete(account_session)
        session.commit()
    else:  # если аккаунта не существует, выбрасываем 404
        abort(404)
    return redirect('/market')


@app.route('/market/<category>', methods=['POST', 'GET'])  # сортировка аккаунтов по категориям
def sorted_market(category):
    session = db_session.create_session()
    is_my = False
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
    elif category == 'my':
        account_session = session.query(accounts.Accounts).filter(accounts.Accounts.user_id
                                                                  == current_user.id)
        is_my = True
    else:
        account_session = session.query(accounts.Accounts).filter(accounts.Accounts.type
                                                                  == 'Other')
    account_dict = {}  # словарь аккаунтов
    for account in account_session[::-1]:
        account_dict[account.title] = [account.price, 1, account.link,
                                       account.user_name, account.type.lower(), account.id,
                                       str(account.created_date).split()[0].split('-'),
                                       account.about_acc,
                                       str(account.created_date).split()[1].split('.')[0].split(
                                           ':')]
    if current_user.is_authenticated:
        return render_template('market.html',
                               name=current_user.name,
                               photo='/'.join(current_user.photo.split('/')[1:]),
                               account_dict=account_dict,
                               is_photo=current_user.is_photo, ADMINS=ADMINS,
                               title=f'Аккаунты: {category.title()}', is_my=is_my)
    return render_template('market.html',
                           account_dict=account_dict,
                           title=f'Аккаунты: {category.title()}')


if __name__ == '__main__':
    db_session.global_init("db/logins.db")
    #port = int(os.environ.get("PORT", 5000))
    #app.run(host='0.0.0.0', port=port)
    app.run()
