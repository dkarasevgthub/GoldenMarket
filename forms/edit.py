from flask_wtf import FlaskForm
from wtforms import PasswordField, SubmitField, StringField, SelectField
from wtforms.validators import DataRequired


class RedactMailForm(FlaskForm):  # форма редактирования почты
    email_new = StringField('Новая почта', validators=[DataRequired()])
    submit = SubmitField('Изменить данные')


class RedactPasswordForm(FlaskForm):  # форма редактирования пароля
    password_old = PasswordField('Старый пароль', validators=[DataRequired()])
    password_new = PasswordField('Новый пароль', validators=[DataRequired()])
    submit = SubmitField('Изменить данные')


class RedactNameForm(FlaskForm):  # форма редактирования имени пользователя
    name_new = StringField('Новое имя пользователя', validators=[DataRequired()])
    submit = SubmitField('Изменить данные')


class MarketForm(FlaskForm):  # форма маркета
    name = StringField('Название товара:')
    category = SelectField('Категория:',
                           choices=[('VK', 'VK'), ('Steam', 'Steam'),
                                    ('Instagram', 'Instagram'), ('Origin', 'Origin'),
                                    ('Mail', 'Mail'), ('Other', 'Other')])
    about = StringField('Описание аккаунта:')
    price = StringField('Цена аккаунта(ов):')
    link = StringField('Ссылка на ваши контакты (ВК, Инстаграм и др) с протоколом https:')
    submit = SubmitField('Выставить на продажу')
