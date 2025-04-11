import unittest
from flask_testing import TestCase
from website import create_app, db
from website .models import User


class TestAuth(TestCase):

    def create_app(self):
        app = create_app()
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        return app

    def setUp(self):
        db.create_all()
        self.user_data = {
            'email': 'test@example.com',
            'first_name': 'Test',
            'password': 'test_password',
            'role': 'customer'
        }

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_login_successful(self):

        user = User(**self.user_data)
        db.session.add(user)
        db.session.commit()

        response = self.client.post('/login', data={
            'email': 'test@example.com',
            'password': 'test_password',
        }, follow_redirects=True)

        self.assertTrue(user.is_authenticated)

        self.assertStatus(response, 200)

    def test_login_incorrect_password(self):

        user = User(**self.user_data)
        db.session.add(user)
        db.session.commit()

        response = self.client.post('/login', data={
            'email': 'test@example.com',
            'password': 'incorrect_password',
        }, follow_redirects=True)

        with self.client.session_transaction() as session:
            self.assertIsNone(session.get('user_id'))

    def test_login_email_not_exist(self):

        response = self.client.post('/login', data={
            'email': 'nonexistent@example.com',
            'password': 'some_password',
        }, follow_redirects=True)

        with self.client.session_transaction() as session:
            self.assertIsNone(session.get('user_id'))

    def test_logout(self):

        user = User(**self.user_data)
        db.session.add(user)
        db.session.commit()

        response = self.client.post('/login', data={
            'email': 'test@example.com',
            'password': 'test_password',
        }, follow_redirects=True)

        self.assertTrue(user.is_authenticated)

        response = self.client.get('/logout', follow_redirects=True)

        self.assertTemplateUsed('login.html')

        with self.client.session_transaction() as session:
            self.assertNotIn('user_id', session)

    def test_sign_up_successful(self):
        response = self.client.post('/sign-up', data={
            'email': 'new_user@example.com',
            'firstName': 'New',
            'password1': 'new_password',
            'password2': 'new_password',
        }, follow_redirects=True)

        self.assertTemplateUsed('uzrasai_page.html')

        new_user = User.query.filter_by(email='new_user@example.com').first()
        self.assertTrue(new_user.is_authenticated)

        self.assertEqual(new_user.email, 'new_user@example.com')
        self.assertEqual(new_user.first_name, 'New')
        self.assertEqual(new_user.role, 'customer')

    def test_sign_up_existing_email(self):
        existing_user = User(email='existing_user@example.com', first_name='Existing', password='existing_password')
        db.session.add(existing_user)
        db.session.commit()

        response = self.client.post('/sign-up', data={
            'email': 'existing_user@example.com',
            'firstName': 'New',
            'password1': 'new_password',
            'password2': 'new_password',
        }, follow_redirects=True)

        self.assertMessageFlashed('Email already exists.', 'error')

        self.assertFalse(self.get_context_variable('user').is_authenticated)

        existing_user_updated = User.query.filter_by(email='existing_user@example.com').first()
        self.assertEqual(existing_user_updated.first_name, 'Existing')
        self.assertEqual(existing_user_updated.password, 'existing_password')

    def test_sign_up_short_email(self):
        response = self.client.post('/sign-up', data={
            'email': 'a@b',
            'firstName': 'New',
            'password1': 'new_password',
            'password2': 'new_password',
        }, follow_redirects=True)

        self.assertMessageFlashed('Email must be greater than 3 characters.', 'error')

        self.assertFalse(self.get_context_variable('user').is_authenticated)

    def test_sign_up_short_first_name(self):

        response = self.client.post('/sign-up', data={
            'email': 'new_user@example.com',
            'firstName': 'N',
            'password1': 'new_password',
            'password2': 'new_password',
        }, follow_redirects=True)

        self.assertFalse(self.get_context_variable('user').is_authenticated)

    def test_sign_up_passwords_not_match(self):

        response = self.client.post('/sign-up', data={
            'email': 'new_user@example.com',
            'firstName': 'New',
            'password1': 'password123',
            'password2': 'different_password',
        }, follow_redirects=True)

        self.assertFalse(self.get_context_variable('user').is_authenticated)

    def test_admin_page_access(self):
        user = User(email='regular_user@example.com', first_name='Regular', password='regular_password')
        db.session.add(user)
        db.session.commit()

        self.client.post('/login', data={
            'email': 'regular_user@example.com',
            'password': 'regular_password',
        }, follow_redirects=True)

        response = self.client.get('/admin-page', follow_redirects=True)

        self.assertNotIn('naudotojai.html', response.data.decode())


if __name__ == '__main__':
    unittest.main()
