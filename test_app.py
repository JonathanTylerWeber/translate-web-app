import json
from flask import Flask
from app import app, db, Searches, User
from flask_bcrypt import Bcrypt
import unittest
from unittest import TestCase

app.config['WTF_CSRF_ENABLED'] = False

class BaseTestCase(TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///translate_test'
        self.app = app.test_client()
        self.bcrypt = Bcrypt(app)
        self.setUpDatabase()

    def tearDown(self):
        self.tearDownDatabase()

    def setUpDatabase(self):
        with app.app_context():
            db.create_all()

            # Create a test user with a hashed password
            password = 'password'
            hashed_password = self.bcrypt.generate_password_hash(password).decode('utf-8')
            test_user = User(email='test@example.com', password=hashed_password)
            db.session.add(test_user)
            db.session.commit()

    def tearDownDatabase(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def login(self):
        login_data = {'email': 'test@example.com', 'password': 'password'}
        self.app.post('/login', data=login_data, follow_redirects=True)


class TranslateTestCase(BaseTestCase):

    def test_translate_endpoint(self):
        # Log in the test user
        self.login()

        # Test a valid translation after successful login
        data = {'word': 'hello', 'direction': 'en_to_zh'}
        response = self.app.post('/translate', json=data, follow_redirects=True)

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
            self.assertEqual(pinyin, 'nǐ hǎo')
        else:
            self.fail(f"Unexpected response content type: {response.content_type}")


class HistoryTestCase(BaseTestCase):

    def setUp(self):
        super().setUp()
        self.login()
        # Perform a translation to add a record to the search history
        data = {'word': 'hello', 'direction': 'en_to_zh'}
        response = self.app.post('/translate', json=data, follow_redirects=True)

    def test_history_endpoint(self):
        # Access the history page
        response = self.app.get('/history')
        response = self.app.get('/history', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        # Check if the word 'hello' is present in the response content
        self.assertIn(b'hello', response.data)


if __name__ == '__main__':
    unittest.main()
