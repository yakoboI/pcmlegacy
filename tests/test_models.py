"""
Tests for database models
"""

import pytest
from datetime import datetime, timezone
from models import User, Category, Material, SubscriptionPlan, db


class TestUser:
    """Test User model"""
    
    def test_user_creation(self, client):
        """Test user creation"""
        with client.application.app_context():
            user = User(
                email='newuser@example.com',
                first_name='New',
                last_name='User',
                is_active=True
            )
            user.set_password('password123')
            db.session.add(user)
            db.session.commit()
            
            assert user.id is not None
            assert user.email == 'newuser@example.com'
            assert user.is_active is True
            assert user.is_admin is False
    
    def test_password_hashing(self, client):
        """Test password hashing"""
        with client.application.app_context():
            user = User(
                email='test@example.com',
                first_name='Test',
                last_name='User'
            )
            user.set_password('password123')
            
            assert user.password_hash != 'password123'
            assert user.check_password('password123') is True
            assert user.check_password('wrongpassword') is False
    
    def test_get_full_name(self, client):
        """Test get_full_name method"""
        with client.application.app_context():
            user = User(
                email='test@example.com',
                first_name='John',
                last_name='Doe'
            )
            assert user.get_full_name() == 'John Doe'


class TestCategory:
    """Test Category model"""
    
    def test_category_creation(self, client):
        """Test category creation"""
        with client.application.app_context():
            category = Category(
                name='Mathematics',
                description='Math materials',
                is_active=True
            )
            db.session.add(category)
            db.session.commit()
            
            assert category.id is not None
            assert category.name == 'Mathematics'
            assert category.is_active is True


class TestMaterial:
    """Test Material model"""
    
    def test_material_creation(self, client, test_category):
        """Test material creation"""
        with client.application.app_context():
            # Get category from session
            category = db.session.get(Category, test_category.id)
            material = Material(
                title='Test Material',
                description='Test description',
                category_id=category.id,
                price=5000,
                is_active=True,
                is_free=False
            )
            db.session.add(material)
            db.session.commit()
            
            assert material.id is not None
            assert material.title == 'Test Material'
            assert material.price == 5000
            assert material.is_active is True
            assert material.is_free is False
    
    def test_free_material(self, client, test_category):
        """Test free material"""
        with client.application.app_context():
            # Get category from session
            category = db.session.get(Category, test_category.id)
            material = Material(
                title='Free Material',
                description='Free description',
                category_id=category.id,
                price=0,
                is_active=True,
                is_free=True
            )
            db.session.add(material)
            db.session.commit()
            
            assert material.is_free is True
            assert material.price == 0


class TestSubscriptionPlan:
    """Test SubscriptionPlan model"""
    
    def test_subscription_plan_creation(self, client):
        """Test subscription plan creation"""
        with client.application.app_context():
            plan = SubscriptionPlan(
                name='Basic Plan',
                description='Basic subscription',
                price=10000,
                duration_days=30,
                max_materials=50,
                is_active=True
            )
            db.session.add(plan)
            db.session.commit()
            
            assert plan.id is not None
            assert plan.name == 'Basic Plan'
            assert plan.price == 10000
            assert plan.duration_days == 30

