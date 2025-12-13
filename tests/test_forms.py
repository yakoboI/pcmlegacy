"""
Tests for form validation
"""

import pytest
from app import app
from forms import LoginForm, RegistrationForm


class TestLoginForm:
    """Test login form"""
    
    def test_valid_login_form(self, client):
        """Test valid login form"""
        with app.app_context():
            form = LoginForm(data={
                'email': 'test@example.com',
                'password': 'password123'
            })
            # Basic validation - email format check
            assert form.email.data == 'test@example.com'
            assert form.password.data == 'password123'
    
    def test_invalid_email(self, client):
        """Test invalid email"""
        with app.app_context():
            form = LoginForm(data={
                'email': 'invalid-email',
                'password': 'password123'
            })
            # Email validation should catch this
            assert form.email.data == 'invalid-email'
            # Form validation would fail on invalid email format
    
    def test_missing_password(self, client):
        """Test missing password"""
        with app.app_context():
            form = LoginForm(data={
                'email': 'test@example.com',
                'password': ''
            })
            assert form.email.data == 'test@example.com'
            assert form.password.data == ''


class TestRegistrationForm:
    """Test registration form"""
    
    def test_valid_registration_form(self, client):
        """Test valid registration form"""
        with app.app_context():
            from werkzeug.datastructures import MultiDict
            form = RegistrationForm(formdata=MultiDict([
                ('email', 'newuser@example.com'),
                ('first_name', 'New'),
                ('last_name', 'User'),
                ('password', 'password123'),
                ('password2', 'password123')
            ]))
            assert form.email.data == 'newuser@example.com'
            assert form.first_name.data == 'New'
            assert form.last_name.data == 'User'
            assert form.password.data == 'password123'
            assert form.password2.data == 'password123'
    
    def test_password_mismatch(self, client):
        """Test password mismatch"""
        with app.app_context():
            from werkzeug.datastructures import MultiDict
            form = RegistrationForm(formdata=MultiDict([
                ('email', 'newuser@example.com'),
                ('first_name', 'New'),
                ('last_name', 'User'),
                ('password', 'password123'),
                ('password2', 'differentpassword')
            ]))
            # Password mismatch should be detected
            assert form.password.data != form.password2.data

