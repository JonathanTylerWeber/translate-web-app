import os
import unittest
from models import db, User, Searches
from flask_bcrypt import Bcrypt
from sqlalchemy import exc
from app import app

# Set the environmental variable for the test database
os.environ['DATABASE_URL'] = "postgresql:///translate_test"

class UserModelTestCase(unittest.TestCase):

    def setUp(self):
        """Create test client, add sample data."""
        db.create_all()
        User.query.delete()
        Searches.query.delete()
        self.client = app.test_client()

    def tearDown(self):
        db.session.rollback()
        db.session.remove()

    def test_user_model(self):
        """Does basic model work?"""
        u = User(email="test@test.com", password="HASHED_PASSWORD")
        db.session.add(u)
        db.session.commit()
        self.assertEqual(len(u.user_searches), 0)

    def test_repr(self):
        user = User(email='test@example.com')
        expected_repr = f"<User #{user.id}: {user.email}>"
        self.assertEqual(repr(user), expected_repr)

    def test_signup_with_valid_credentials(self):
        email = 'testuser@example.com'
        password = 'password123'
        new_user = User.signup(email, password)
        db.session.commit()
        self.assertIsNotNone(new_user)
        self.assertEqual(new_user.email, email)
        bcrypt = Bcrypt()
        self.assertNotEqual(new_user.password, password)
        self.assertTrue(bcrypt.check_password_hash(new_user.password, password))

    def test_invalid_email_signup(self):
        invalid = User.signup(None, "password")
        uid = 123789
        invalid.id = uid
        with self.assertRaises(exc.IntegrityError):
            db.session.commit()

    def test_invalid_password_signup(self):
        with self.assertRaises(ValueError):
            User.signup("email@email.com", "")
        with self.assertRaises(ValueError):
            User.signup("email@email.com", None)

    def test_authenticate_with_valid_credentials(self):
        email = 'testuser@example.com'
        password = 'password123'
        user = User.signup(email, password)
        db.session.commit()
        authenticated_user = User.authenticate(email, password)
        self.assertNotEqual(authenticated_user, False)
        self.assertEqual(authenticated_user.email, user.email)

    def test_authenticate_with_invalid_email(self):
        authenticated_user = User.authenticate('invalidemail', 'password123')
        self.assertEqual(authenticated_user, False)

    def test_authenticate_with_invalid_password(self):
        email = 'testuser@example.com'
        password = 'password123'
        User.signup(email, password)
        db.session.commit()
        authenticated_user = User.authenticate(email, 'invalidpassword')
        self.assertEqual(authenticated_user, False)

if __name__ == '__main__':
    unittest.main()
