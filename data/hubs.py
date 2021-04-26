import sqlalchemy
from .db_session import SqlAlchemyBase
from sqlalchemy import orm


class Hubs(SqlAlchemyBase):
    __tablename__ = 'hubs'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    admin = sqlalchemy.Column(sqlalchemy.Integer,
                                sqlalchemy.ForeignKey("users.id"))
    name = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    requests = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    user = orm.relation('User')