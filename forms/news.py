from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField
from wtforms import BooleanField, SubmitField
from wtforms.validators import DataRequired


class NewsForm(FlaskForm):
    title = StringField('Заголовок', validators=[DataRequired()])
    content = TextAreaField("Содержание")
    id_user = StringField("ID пользователя", validators=[DataRequired()])
    is_private = BooleanField("Личное")
    submit = SubmitField('Применить')