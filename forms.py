from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, RadioField, SubmitField
from wtforms.validators import DataRequired, Email, Length


class UserForm(FlaskForm):
    """Form for adding users."""

    email = StringField('E-mail', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[Length(min=6)])

class TranslateForm(FlaskForm):
    """Form for translating."""

    word = StringField('Translate', validators=[DataRequired()])
    # direction = RadioField('Translation Direction', choices=[('en_to_zh', 'English to Chinese'), ('zh_to_en', 'Chinese to English')], default='en_to_zh')
    # submit = SubmitField('Go')
