from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, RadioField, SubmitField, validators
from wtforms.validators import DataRequired, Email, Length


class UserForm(FlaskForm):
    """Form for adding users."""

    email = StringField('E-mail', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[Length(min=6)])


class TranslateForm(FlaskForm):
    """Form for translating."""

    word = TextAreaField('Translate', validators=[DataRequired()], render_kw={"placeholder": "Enter English text..."})


class PasswordResetRequestForm(FlaskForm):
    email = StringField('Email', validators=[validators.DataRequired(), validators.Email()])

