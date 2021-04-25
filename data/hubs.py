import sqlalchemy
from .db_session import SqlAlchemyBase


class Hubs(SqlAlchemyBase):
    __tablename__ = 'hubs'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    admin = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=True)