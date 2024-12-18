from google.cloud import translate_v2 as translate
from google.oauth2 import service_account

import requests

import os, json

from flask import Flask, render_template, request, flash, redirect, session, g, url_for, jsonify
from flask_debugtoolbar import DebugToolbarExtension 
from flask_bcrypt import Bcrypt
from sqlalchemy.exc import IntegrityError
import re
import secrets
from xpinyin import Pinyin
from mailjet_rest import Client

from forms import UserForm, TranslateForm, PasswordResetRequestForm
from models import db, connect_db, User, Searches, PasswordResetRequest

from dotenv import load_dotenv
load_dotenv()

bcrypt = Bcrypt()
p = Pinyin()

# CREDENTIALS = json.loads(os.getenv('CREDENTIALS'))

# if os.path.exists('credentials.json'):
#     print("no credentials file found")
#     pass
# else:
#     print("write credentials")
#     with open('credentials.json', 'w') as credFile:
#         json.dump(CREDENTIALS, credFile)

# os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'credentials.json'

# new creds
# Load the credentials from the environment variable (as JSON string)
credentials_info = json.loads(os.getenv('CREDENTIALS'))

# Create credentials using the correct method
credentials = service_account.Credentials.from_service_account_info(credentials_info)

# Initialize the translate client with the credentials
translateClient = translate.Client(credentials=credentials)

api_key = os.environ['MJ_APIKEY_PUBLIC']
api_secret = os.environ['MJ_APIKEY_PRIVATE']
mailjet = Client(auth=(api_key, api_secret), version='v3.1')

# translateClient = translate.Client()

CURR_USER_KEY = "curr_user"

app = Flask(__name__)
print(os.environ.get('DATABASE_URL', ''))
app.config['SQLALCHEMY_DATABASE_URI'] = (
    os.environ.get('DATABASE_URL', ''))

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', "it's a secret")

# toolbar = DebugToolbarExtension(app)

with app.app_context():
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
    return render_template('start.html')
  
@app.route('/translate')
def home():
    """display translate page"""
    if not g.user:
        flash("Must sign in first", "danger")
        return redirect("/signup")

    form = TranslateForm()

    return render_template('home.html', form=form)

@app.route('/test-public-api', methods=["GET"])
def test_public_api():
    """Hit a simple public API and return the response."""
    try:
        # Make a GET request to a public API
        response = requests.get('https://jsonplaceholder.typicode.com/todos')

        # Check if the request was successful
        if response.status_code == 200:
            return jsonify(response.json()), 200
        else:
            return jsonify({'error': f'Failed to fetch data from public API. Status code: {response.status_code}'}), 500

    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=["POST"])
def health():
    # Get the JSON data sent in the POST request (if necessary)
    request_data = request.get_json()

    # Print the received request data (optional, for debugging)
    print("Received request data:", request_data)
    
    try:
        # Open and read the credentials.json file
        with open('credentials.json', 'r') as cred_file:
            credentials = json.load(cred_file)
        
        # Return the contents of credentials.json as JSON
        return jsonify(credentials), 200

    except FileNotFoundError:
        return jsonify({'error': 'credentials.json file not found'}), 404
    except json.JSONDecodeError:
        return jsonify({'error': 'Error decoding credentials.json'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500



@app.route('/translate', methods=["POST"])
def translate():
    """translate input"""
    print("start translate")
    if not g.user:
        print("bad user")
        flash("Must sign in first", "danger")
        return redirect("/signup")

    try:
        print("start try")
        if request.is_json:
            data = request.get_json()
            word = data.get('word')
            direction = data.get('direction')
        else:
            word = request.form.get('word')
            direction = request.form.get('direction')

        if word is None or direction is None:
            print("bad word")
            app.logger.error('Invalid request data')
            return jsonify({'error': 'Invalid request data'})

        if direction == 'en_to_zh':
            print("en to zh")
            
            detectResponse = translateClient.detect_language(word)
            print("detect response ***********")
            print(detectResponse)
            translateResponse = translateClient.translate(word, 'zh')
            pinyin = p.get_pinyin(translateResponse['translatedText'], splitter=' ', tone_marks='marks')
        else:
            print("zh to en")
            detectResponse = translateClient.detect_language(word)
            translateResponse = translateClient.translate(word, 'en')
            pinyin = p.get_pinyin(word, splitter=' ', tone_marks='marks')

        word_lang = detectResponse['language']
        translation_text = translateResponse['translatedText']
        print("out of if elses")
        search = Searches(
            word=word,
            word_lang=word_lang,
            translation=translation_text,
            pinyin=pinyin,
            user_id=g.user.id
        )
        print("write to db")
        db.session.add(search)
        db.session.commit()
        print("write to res")
        response_data = {
            'translation': translation_text,
            'pinyin': pinyin
        }
    except Exception as e:
        app.logger.exception('An error occurred during translation:')
        return jsonify({'error': str(e)})
    print("return json res")
    return jsonify(response_data)


@app.route('/history')
def show_history_page():
    """display search history page"""
    if not g.user:
        flash("Must sign in first", "danger")
        return redirect("/signup")

    searches = Searches.query.filter_by(user_id=g.user.id).order_by(Searches.id.desc()).all()
    return render_template('history.html', searches=searches)


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

        return redirect("/translate")

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
            return redirect("/translate")

        flash("Invalid credentials.", 'danger')

    return render_template('login.html', form=form)


@app.route('/logout')
def logout():
    """Handle logout of user."""

    do_logout()

    flash("You have successfully logged out.", 'success')
    return redirect("/login")


@app.route('/reset-password-request', methods=['GET', 'POST'])
def reset_password_request():
    form = PasswordResetRequestForm()

    if form.validate_on_submit():
        email = form.email.data
        user = User.query.filter_by(email=email).first()
        # Generate a unique token
        token = secrets.token_urlsafe(20)

        # Save the token to the database
        reset_request = PasswordResetRequest(email=email, token=token)
        db.session.add(reset_request)
        db.session.commit()

        # Send the password reset email
        send_password_reset_email(email, token)

        flash('An email has been sent with instructions to reset your password. (It may be in your spam folder)', 'info')
        return redirect(url_for('login'))

    return render_template('reset_password_request.html', form=form)

def send_password_reset_email(email, token):
    data = {
        'Messages': [
                        {
                                "From": {
                                        "Email": "jonathantweber@gmail.com",
                                        "Name": "Me"
                                },
                                "To": [
                                        {
                                                "Email": email,
                                                "Name": "You"
                                        }
                                ],
                                "Subject": 'Password Reset Request',
                                "TextPart": f'Click the following link to reset your password: {url_for("reset_password", token=token, _external=True)}',
                        }
                ]
    }
    result = mailjet.send.create(data=data)
    print(result.status_code)
    print(result.json())


@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    reset_request = PasswordResetRequest.query.filter_by(token=token).first()

    if reset_request:
        # Add a form for users to enter a new password
        form = UserForm()

        if form.validate_on_submit():
            # Update the user's password
            user = User.query.filter_by(email=reset_request.email).first()
            user.password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
            
            # Delete the reset request
            db.session.delete(reset_request)
            db.session.commit()

            flash('Your password has been reset successfully.', 'success')
            return redirect(url_for('login'))

        return render_template('reset_password.html', form=form)

    flash('Invalid or expired reset link.', 'danger')
    return redirect(url_for('login'))


@app.route('/history/<int:search_id>/save', methods=["POST"])
def save_unsave_search(search_id):
    """Save or unsave a search."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return jsonify({'error': 'Access unauthorized'}), 401

    search = Searches.query.get(search_id)

    if not search or search.user_id != g.user.id:
        flash("Search not found or unauthorized.", "danger")
        return jsonify({'error': 'Search not found or unauthorized'}), 404

    # Toggle the is_saved state
    search.is_saved = not search.is_saved

    db.session.commit()

    return jsonify({'message': 'Search saved/unsaved successfully'})


@app.route('/saved-searches')
def saved_searches():
    if not g.user:
        flash("Access unauthorized.", "danger")
        return jsonify({'error': 'Access unauthorized'}), 401
    saved_searches = Searches.query.filter_by(user_id=g.user.id, is_saved=True).order_by(Searches.id.desc()).all()
    return render_template('saved_searches.html', searches=saved_searches)



@app.route('/history/<int:search_id>/delete', methods=["DELETE"])
def delete_search(search_id):
    """Delete a search."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return jsonify({'error': 'Access unauthorized'}), 401

    search = Searches.query.get(search_id)

    if not search or search.user_id != g.user.id:
        flash("Search not found or unauthorized.", "danger")
        return jsonify({'error': 'Search not found or unauthorized'}), 404

    db.session.delete(search)
    db.session.commit()

    return jsonify({'message': 'Search deleted successfully'})


@app.after_request
def add_header(req):
    """Add non-caching headers on every request."""

    req.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    req.headers["Pragma"] = "no-cache"
    req.headers["Expires"] = "0"
    req.headers['Cache-Control'] = 'public, max-age=0'
    return req
