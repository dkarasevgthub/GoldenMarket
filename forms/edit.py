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
    count = SelectField('Количество товара (от 1 до 20):',
                        choices=[('1', '1'), ('2', '2'), ('3', '3'),
                                 ('4', '4'), ('5', '5'), ('8', '8'),
                                 ('6', '6'), ('7', '7'), ('9', '9'),
                                 ('10', '10'), ('11', '11'), ('12', '12'),
                                 ('13', '13'), ('14', '14'), ('15', '15'),
                                 ('16', '16'), ('17', '17'), ('18', '18'),
                                 ('19', '19'), ('20', '20')])
    about = StringField('Описание аккаунта:')
    price = StringField('Цена аккаунта(ов):')
    link = StringField('Ссылка на ваши контакты (ВК, Инстаграм и др) с протоколом https:')
    submit = SubmitField('Выставить на продажу')
