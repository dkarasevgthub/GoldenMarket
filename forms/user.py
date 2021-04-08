from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired


class RegisterForm(FlaskForm):
    email = StringField('Введите почту', validators=[DataRequired()])
    password = PasswordField('Придумайте пароль',  validators=[DataRequired()])
    password_again = PasswordField('Повторите пароль', validators=[DataRequired()])
    name = StringField('Введите имя пользователя', validators=[DataRequired()])
    submit = SubmitField('Зарегистрироваться')
