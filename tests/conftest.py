"""
Pytest configuration and fixtures
"""

import pytest
import os
import tempfile
from pathlib import Path

# Set test environment
os.environ['FLASK_ENV'] = 'testing'
os.environ['SECRET_KEY'] = 'test-secret-key-for-testing-only'
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'

from app import app, db
from models import User, Category, Material, SubscriptionPlan
from flask_login import FlaskLoginClient


@pytest.fixture(scope='function')
def client():
    """Create a test client"""
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.session.remove()
            db.drop_all()


@pytest.fixture
def test_user(client):
    """Create a test user"""
    with app.app_context():
        user = User(
            email='test@example.com',
            first_name='Test',
            last_name='User',
            is_active=True,
            is_admin=False
        )
        user.set_password('testpassword123')
        db.session.add(user)
        db.session.commit()
        # Expunge and refresh to avoid detached instance errors
        user_id = user.id
        db.session.expunge(user)
        # Return fresh object from session
        return db.session.get(User, user_id)


@pytest.fixture
def admin_user(client):
    """Create an admin test user"""
    with app.app_context():
        user = User(
            email='admin@example.com',
            first_name='Admin',
            last_name='User',
            is_active=True,
            is_admin=True
        )
        user.set_password('adminpassword123')
        db.session.add(user)
        db.session.commit()
        # Expunge and refresh to avoid detached instance errors
        user_id = user.id
        db.session.expunge(user)
        # Return fresh object from session
        return db.session.get(User, user_id)


@pytest.fixture
def test_category(client):
    """Create a test category"""
    with app.app_context():
        category = Category(
            name='Test Category',
            description='Test category description',
            is_active=True
        )
        db.session.add(category)
        db.session.commit()
        # Expunge and refresh to avoid detached instance errors
        category_id = category.id
        db.session.expunge(category)
        # Return fresh object from session
        return db.session.get(Category, category_id)


@pytest.fixture
def test_material(client, test_category):
    """Create a test material"""
    with app.app_context():
        # Ensure category is in session
        category = db.session.get(Category, test_category.id)
        material = Material(
            title='Test Material',
            description='Test material description',
            category_id=category.id,
            price=1000,
            is_active=True,
            is_free=False
        )
        db.session.add(material)
        db.session.commit()
        material_id = material.id
        db.session.expunge(material)
        # Return fresh object from session
        return db.session.get(Material, material_id)


@pytest.fixture
def authenticated_client(client, test_user):
    """Create an authenticated test client"""
    with app.app_context():
        user_id = test_user.id if hasattr(test_user, 'id') else test_user
        with client.session_transaction() as sess:
            sess['_user_id'] = str(user_id)
            sess['_fresh'] = True
    return client


@pytest.fixture
def admin_client(client, admin_user):
    """Create an authenticated admin test client"""
    with app.app_context():
        user_id = admin_user.id if hasattr(admin_user, 'id') else admin_user
        with client.session_transaction() as sess:
            sess['_user_id'] = str(user_id)
            sess['_fresh'] = True
    return client


@pytest.fixture
def temp_upload_dir():
    """Create a temporary upload directory"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)

