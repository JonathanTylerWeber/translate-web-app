from google.cloud import translate_v2 as translate

import os, json

from flask import Flask, render_template, request, flash, redirect, session, g, url_for, jsonify
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

app.config['SQLALCHEMY_DATABASE_URI'] = (
    os.environ.get('DATABASE_URL', 'postgresql:///translate'))

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', "it's a secret")
toolbar = DebugToolbarExtension(app)

connect_db(app)
db.create_all()

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


@app.route('/')
def take_home():
    return redirect('/translate')
  
@app.route('/translate')
def home():
    """display translate page"""
    form = TranslateForm()

    return render_template('home.html', form=form)


@app.route('/translate', methods=["POST"])
def translate():
    """translate input"""
    try:
        if request.is_json:
            data = request.get_json()
            word = data.get('word')
            direction = data.get('direction')
        else:
            # Handle form data
            word = request.form.get('word')
            direction = request.form.get('direction')

        if word is None or direction is None:
            app.logger.error('Invalid request data')
            return jsonify({'error': 'Invalid request data'})

        if direction == 'en_to_zh':
            detectResponse = translateClient.detect_language(word)
            translateResponse = translateClient.translate(word, 'zh')
            pinyin = search_word_in_file(translateResponse['translatedText'])
        else:
            detectResponse = translateClient.detect_language(word)
            translateResponse = translateClient.translate(word, 'en')
            pinyin = search_word_in_file(word)

        word_lang = detectResponse['language']
        translation_text = translateResponse['translatedText']

        search = Searches(
            word=word,
            word_lang=word_lang,
            translation=translation_text,
            pinyin=pinyin,
            user_id=g.user.id
        )

        db.session.add(search)
        db.session.commit()

        response_data = {
            'translation': translation_text,
            'pinyin': pinyin
        }
    except Exception as e:
        app.logger.exception('An error occurred during translation:')
        return jsonify({'error': str(e)})

    return jsonify(response_data)



@app.route('/history')
def show_history_page():
    """display search history page"""
    searches = (Searches.query.filter(Searches.user_id == g.user.id).all())
    return render_template('history.html', searches=searches)


def search_word_in_file(input_word):
    """return pinyin for words"""
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
