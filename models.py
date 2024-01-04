from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
import secrets
from sqlalchemy import Column

bcrypt = Bcrypt()
db = SQLAlchemy()


class User(db.Model):
    """User in the system."""

    __tablename__ = 'users'

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    email = db.Column(
        db.Text,
        nullable=False,
        unique=True,
    )

    password = db.Column(
        db.Text,
        nullable=False,
    )

    

    def __repr__(self):
        return f"<User #{self.id}: {self.email}>"

    @classmethod
    def signup(cls, email, password):
        """Sign up user.

        Hashes password and adds user to system.
        """

        hashed_pwd = bcrypt.generate_password_hash(password).decode('utf-8')

        user = User(
            email=email,
            password=hashed_pwd,
        )

        db.session.add(user)
        return user

    @classmethod
    def authenticate(cls, email, password):
        """Find user with `email` and `password`"""

        user = cls.query.filter_by(email=email).first()

        if user:
            is_auth = bcrypt.check_password_hash(user.password, password)
            if is_auth:
                return user

        return False

class Searches(db.Model):
    """user searches"""

    __tablename__ = 'searches'

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    word = db.Column(
        db.Text,
        nullable=False
    )

    word_lang = db.Column(
        db.Text,
        nullable=False
    )

    translation = db.Column(
        db.Text,
        nullable=False
    )

    pinyin = db.Column(
        db.Text
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
    )

    user = db.relationship(
        'User',
        backref='user_searches'
    )

    is_saved = db.Column(
        db.Boolean,
        default=False,
        nullable=False
    )

class PasswordResetRequest(db.Model):
    __tablename__ = 'password_reset_requests'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    token = db.Column(db.String(50), nullable=False, unique=True)


def connect_db(app):
    """Connect database"""

    db.app = app
    db.init_app(app)