from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, SubmitField, URLField
from wtforms.validators import DataRequired


class Password(FlaskForm):
    password = StringField("Пароль", validators=[DataRequired()])
    submit = SubmitField('Отправить')
