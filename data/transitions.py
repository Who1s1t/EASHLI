import datetime
import sqlalchemy
from sqlalchemy import orm
from sqlalchemy_serializer import SerializerMixin
from werkzeug.security import generate_password_hash, check_password_hash

from .db_session import SqlAlchemyBase


class Transition(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'transitions'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    created_date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)

    link_id = sqlalchemy.Column(sqlalchemy.Integer,
                                sqlalchemy.ForeignKey("links.id"))
    link = orm.relationship('Link')
