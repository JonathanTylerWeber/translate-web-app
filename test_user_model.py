"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase

from models import db, User, Searches
from flask_bcrypt import Bcrypt
from sqlalchemy import exc

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///translate_test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


class UserModelTestCase(TestCase):
   
    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Searches.query.delete()

        self.client = app.test_client()

    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res

    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no searches
        self.assertEqual(len(u.user_searches), 0)

    def test_repr(self):
        user = User(email='test@example.com')
        expected_repr = f"<User #{user.id}: {user.email}>"
        self.assertEqual(repr(user), expected_repr)

    def test_signup_with_valid_credentials(self):
        # Provide valid credentials for the new user
        email = 'testuser@example.com'
        password = 'password123'

        # Call the User.signup() method to create a new user
        new_user = User.signup(email, password)
        db.session.commit()

        # Assert that the new user is not None, indicating successful signup
        self.assertIsNotNone(new_user)

        # Assert that the new user's username match the provided credentials
        self.assertEqual(new_user.email, email)

        # Get an instance of Bcrypt
        bcrypt = Bcrypt()

        # Assert that the new user's password is properly hashed and not equal to the original password
        self.assertNotEqual(new_user.password, password)
        self.assertTrue(bcrypt.check_password_hash(new_user.password, password))

    def test_invalid_email_signup(self):
        invalid = User.signup(None, "password")
        uid = 123789
        invalid.id = uid
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()
    
    def test_invalid_password_signup(self):
        with self.assertRaises(ValueError) as context:
            User.signup("email@email.com", "")
        
        with self.assertRaises(ValueError) as context:
            User.signup("email@email.com", None)

    def test_authenticate_with_valid_credentials(self):
        # Create a new user with valid credentials
        email = 'testuser@example.com'
        password = 'password123'
        user = User.signup(email, password)
        db.session.commit()

        # Call the User.authenticate() method with the valid credentials
        authenticated_user = User.authenticate(email, password)

        # Assert that the authenticated user is not False, indicating successful authentication
        self.assertNotEqual(authenticated_user, False)

        # Assert that the authenticated user is the same as the original user
        self.assertEqual(authenticated_user.email, user.email)

    def test_authenticate_with_invalid_email(self):
        # Call the User.authenticate() method with an invalid email
        authenticated_user = User.authenticate('invalidemail', 'password123')

        # Assert that the authenticated user is False, indicating failed authentication
        self.assertEqual(authenticated_user, False)

    def test_authenticate_with_invalid_password(self):
        # Create a new user with valid credentials
        email = 'testuser@example.com'
        password = 'password123'
        User.signup(email, password)
        db.session.commit()

        # Call the User.authenticate() method with an invalid password
        authenticated_user = User.authenticate(email, 'invalidpassword')

        # Assert that the authenticated user is False, indicating failed authentication
        self.assertEqual(authenticated_user, False)

        