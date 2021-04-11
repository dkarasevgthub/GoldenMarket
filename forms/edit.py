from flask_wtf import FlaskForm
from wtforms import PasswordField, SubmitField, StringField
from wtforms.validators import DataRequired


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
