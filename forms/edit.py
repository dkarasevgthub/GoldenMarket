from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired


class RedactForm(FlaskForm):
    email_new = StringField('Новая почта', validators=[DataRequired()])
    password_old = PasswordField('Старый пароль', validators=[DataRequired()])
    password_new = PasswordField('Новый пароль', validators=[DataRequired()])
    name_new = StringField('Новое имя пользователя', validators=[DataRequired()])
    submit = SubmitField('Изменить данные')
