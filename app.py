from google.cloud import translate_v2 as translate

import os, json

from flask import Flask, render_template, request, flash, redirect, session, g, abort, url_for
from flask_debugtoolbar import DebugToolbarExtension 
from sqlalchemy.exc import IntegrityError
import re

from forms import UserForm, TranslateForm
from models import db, connect_db, User, Searches

from dotenv import load_dotenv
load_dotenv()

CREDENTIALS = json.loads(os.environ.get('CREDENTIALS'))

if os.path.exists('credentials.json'):
    pass
else:
    with open('credentials.json', 'w') as credFile:
        json.dump(CREDENTIALS, credFile)

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'credentials.json'

translateClient = translate.Client()

CURR_USER_KEY = "curr_user"

app = Flask(__name__)

# Get DB_URI from environ variable (useful for production/testing) or,
# if not set there, use development local db.
app.config['SQLALCHEMY_DATABASE_URI'] = (
    os.environ.get('DATABASE_URL', 'postgresql:///translate'))

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', "it's a secret")
toolbar = DebugToolbarExtension(app)

connect_db(app)
db.create_all()

# # detect the language
# detectResponse = translateClient.detect_language('muraho nshuti yanjye')

# print(detectResponse)
# # {'language': 'rw', 'confidence': 1, 'input': 'muraho nshuti yanjye'}

# # translate a phrase
# translateResponse = translateClient.translate('muraho nshuti yanjye', 'en')

# print(translateResponse)
# # {'translatedText': 'hello my friend', 'detectedSourceLanguage': 'rw', 'input': 'muraho nshuti yanjye'}

@app.before_request
def add_user_to_g():
    """If we're logged in, add curr user to Flask global."""

    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])

    else:
        g.user = None


def do_login(user):
    """Log in user."""

    session[CURR_USER_KEY] = user.id


def do_logout():
    """Logout user."""

    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]

  
@app.route('/', methods=["GET", "POST"])
def home():
    """Render home page and handle form submission."""
    form = TranslateForm()  # Create an instance of the TranslateForm

    if form.validate_on_submit():
        word = form.word.data
        detectResponse = translateClient.detect_language(word)
        translateResponse = translateClient.translate(word, 'zh')

        pinyin = search_word_in_file(translateResponse['translatedText'])
        print(f'pinyin: {pinyin}')

        # Store the translation in the session
        session['translation'] = translateResponse['translatedText']
        session['pinyin'] = pinyin

        # Redirect to the home page
        return redirect(url_for('home'))

    # Retrieve translation from session if available
    translation = session.pop('translation', None)
    pinyin = session.pop('pinyin', None)

    return render_template('home.html', form=form, translation=translation, pinyin=pinyin)


def search_word_in_file(input_word):
    file_path = 'pinyin.txt'
    pinyin = ''

    with open(file_path, 'r', encoding='utf-8') as file:
        for char in input_word:
            found = False
            file.seek(0)  # Reset file position to the beginning for each character
            for line in file:
                if char in line:
                    result = line.replace(char, '').strip()
                    pinyin += result + ' '
                    found = True
                    break

            if not found:
                # If the character is not found, use a placeholder
                pinyin += char + ' '

    # Remove trailing space at the end
    pinyin = pinyin.strip()

    # print('**************************')
    # print(f"Pinyin Result: {pinyin}")
    return pinyin




@app.route('/signup', methods=["GET", "POST"])
def signup():
    """Handle user signup.

    Create new user and add to DB. Redirect to home page.

    If form not valid, present form.

    If the there already is a user with that email: flash message
    and re-present form.
    """
    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]
    form = UserForm()

    if form.validate_on_submit():
        try:
            user = User.signup(
                password=form.password.data,
                email=form.email.data,
            )
            db.session.commit()

        except IntegrityError as e:
            flash("Email already taken", 'danger')
            return render_template('signup.html', form=form)

        do_login(user)

        return redirect("/")

    else:
        return render_template('signup.html', form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
    """Handle user login."""

    form = UserForm()

    if form.validate_on_submit():
        user = User.authenticate(form.email.data,
                                 form.password.data)

        if user:
            do_login(user)
            return redirect("/")

        flash("Invalid credentials.", 'danger')

    return render_template('login.html', form=form)


@app.route('/logout')
def logout():
    """Handle logout of user."""

    do_logout()

    flash("You have successfully logged out.", 'success')
    return redirect("/login")

@app.after_request
def add_header(req):
    """Add non-caching headers on every request."""

    req.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    req.headers["Pragma"] = "no-cache"
    req.headers["Expires"] = "0"
    req.headers['Cache-Control'] = 'public, max-age=0'
    return req
