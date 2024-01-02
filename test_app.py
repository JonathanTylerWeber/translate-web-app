import json
from unittest import TestCase
from flask import Flask
from app import app, db, Searches, User, search_word_in_file
from flask_bcrypt import Bcrypt
bcrypt = Bcrypt(app)

app.config['WTF_CSRF_ENABLED'] = False

class TranslateTestCase(TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///translate_test'
        self.app = app.test_client()
        self.setUpDatabase()

    def tearDown(self):
        self.tearDownDatabase()

    def setUpDatabase(self):
        with app.app_context():
            db.create_all()

            # Create a test user with a hashed password
            password = 'password'
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
            test_user = User(email='test@example.com', password=hashed_password)
            db.session.add(test_user)
            db.session.commit()


    def tearDownDatabase(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_translate_endpoint(self):
        # Provide valid login credentials
        login_data = {'email': 'test@example.com', 'password': 'password'}

        # Try to login
        login_response = self.app.post('/login', data=login_data, follow_redirects=True)
        self.assertEqual(login_response.status_code, 200)  # Check if the login is successful

        # Check if the login page contains the user's email (indicating a successful login)
        self.assertIn('translate', login_response.get_data(as_text=True))

        # Test a valid translation after successful login
        data = {'word': 'hello', 'direction': 'en_to_zh'}
        response = self.app.post('/translate', json=data, follow_redirects=True)

        # Print out response data and content type for debugging
        print(response.data)
        print(response.content_type)

        # Check if the response is successful or a redirect
        self.assertIn(response.status_code, [200, 302])

        # Check if the response contains data before trying to load JSON
        if response.content_type == 'application/json':
            result = json.loads(response.data.decode('utf-8'))
            if 'error' in result:
                self.fail(f"Unexpected response content type: {response.content_type}, Data: {response.data.decode('utf-8')}")
            self.assertIn('translation', result)
            self.assertIn('pinyin', result)
            pinyin = result['pinyin']
            self.assertEqual(pinyin, 'ni3 hao3')
        else:
            self.fail(f"Unexpected response content type: {response.content_type}")


class PinyinTestCase(TestCase):

    def test_search_word_in_file(self):
        # Test the search_word_in_file function with a sample word
        input_word = '你好'
        result = search_word_in_file(input_word)

        self.assertIsNotNone(result)
        self.assertIsInstance(result, str)
        self.assertEqual(result, 'ni3 hao3')


class HistoryTestCase(TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///translate_test'
        self.app = app.test_client()
        self.setUpDatabase()

    def tearDown(self):
        self.tearDownDatabase()

    def setUpDatabase(self):
        with app.app_context():
            db.create_all()

            # Create a test user with a hashed password
            password = 'password'
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
            test_user = User(email='test@example.com', password=hashed_password)
            db.session.add(test_user)
            db.session.commit()

            # Log in the test user
            self.login()

            # Perform a translation to add a record to the search history
            data = {'word': 'hello', 'direction': 'en_to_zh'}
            response = self.app.post('/translate', json=data, follow_redirects=True)

    def tearDownDatabase(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def login(self):
        login_data = {'email': 'test@example.com', 'password': 'password'}
        self.app.post('/login', data=login_data, follow_redirects=True)

    def test_history_endpoint(self):
        # Access the history page
        response = self.app.get('/history')
        self.assertEqual(response.status_code, 200)

        # Check if the word 'hello' is present in the response content
        self.assertIn(b'hello', response.data)