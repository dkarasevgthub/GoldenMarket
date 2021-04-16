import sqlalchemy
from .db_session import SqlAlchemyBase
from flask_login import UserMixin
import datetime


class Accounts(SqlAlchemyBase, UserMixin):
    __tablename__ = 'accounts'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True, unique=True)
    created_date = sqlalchemy.Column(sqlalchemy.DateTime,
                                     default=datetime.datetime.now)
    title = sqlalchemy.Column(sqlalchemy.String)
    type = sqlalchemy.Column(sqlalchemy.String)
    price = sqlalchemy.Column(sqlalchemy.String)
    count = sqlalchemy.Column(sqlalchemy.Integer)
    link = sqlalchemy.Column(sqlalchemy.String)
    user_name = sqlalchemy.Column(sqlalchemy.String)
    about_acc = sqlalchemy.Column(sqlalchemy.String)