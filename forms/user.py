from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, TextAreaField, SubmitField, validators
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired


class RegisterForm(FlaskForm):
    email = StringField('Введите почту', [validators.Email()])
    password = PasswordField('Придумайте пароль')
    password_again = PasswordField('Повторите пароль')
    name = StringField('Введите имя пользователя')
    submit = SubmitField('Зарегистрироваться')
