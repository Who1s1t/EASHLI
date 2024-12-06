from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, SubmitField, URLField
from wtforms.validators import DataRequired


class NoLoginLinkForm(FlaskForm):
    link = StringField('Введите ссылку', validators=[DataRequired()])
    alias = StringField("Алиас")
    password = StringField("Пароль")
    submit = SubmitField('Сократить')
