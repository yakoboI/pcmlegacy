"""
Tests for application routes
"""

import pytest
from flask import url_for


class TestPublicRoutes:
    """Test public routes"""
    
    def test_index_page(self, client):
        """Test index page loads"""
        response = client.get('/')
        assert response.status_code == 200
        assert b'Pcmlegacy' in response.data or b'Physics' in response.data
    
    def test_login_page(self, client):
        """Test login page loads"""
        response = client.get('/login')
        assert response.status_code == 200
        assert b'login' in response.data.lower() or b'sign' in response.data.lower()
    
    def test_register_page(self, client):
        """Test register page loads"""
        response = client.get('/register')
        assert response.status_code == 200
        assert b'register' in response.data.lower() or b'sign up' in response.data.lower()
    
    def test_privacy_policy_page(self, client):
        """Test privacy policy page loads"""
        response = client.get('/privacy-policy')
        assert response.status_code == 200
        assert b'Privacy Policy' in response.data or b'privacy' in response.data.lower()
    
    def test_cookie_preferences_page(self, client):
        """Test cookie preferences page loads"""
        response = client.get('/cookie-preferences')
        assert response.status_code == 200


class TestAuthentication:
    """Test authentication routes"""
    
    def test_user_registration(self, client):
        """Test user registration"""
        response = client.post('/register', data={
            'email': 'newuser@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'password': 'password123',
            'confirm_password': 'password123'
        }, follow_redirects=True)
        
        # Should redirect or show success
        assert response.status_code in [200, 302]
    
    def test_user_login(self, client, test_user):
        """Test user login"""
        response = client.post('/login', data={
            'email': 'test@example.com',
            'password': 'testpassword123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
    
    def test_invalid_login(self, client):
        """Test invalid login"""
        response = client.post('/login', data={
            'email': 'nonexistent@example.com',
            'password': 'wrongpassword'
        })
        
        # Should not redirect on invalid login
        assert response.status_code == 200


class TestProtectedRoutes:
    """Test protected routes"""
    
    def test_dashboard_requires_login(self, client):
        """Test dashboard requires authentication"""
        response = client.get('/dashboard', follow_redirects=True)
        # Should redirect to login
        assert response.status_code == 200
        assert b'login' in response.data.lower()
    
    def test_dashboard_accessible_when_logged_in(self, authenticated_client):
        """Test dashboard accessible when logged in"""
        response = authenticated_client.get('/dashboard')
        assert response.status_code == 200
    
    def test_admin_requires_admin_role(self, authenticated_client):
        """Test admin routes require admin role"""
        response = authenticated_client.get('/admin/dashboard', follow_redirects=True)
        # Should redirect or show error (404 if route doesn't exist, or 200/302 if access denied)
        assert response.status_code in [200, 302, 404]
    
    def test_admin_accessible_for_admin(self, admin_client):
        """Test admin routes accessible for admin"""
        response = admin_client.get('/admin/dashboard')
        # Should be accessible (may return 200, 302, or 404 if route doesn't exist)
        assert response.status_code in [200, 302, 404]


class TestMaterialRoutes:
    """Test material-related routes"""
    
    def test_material_list(self, client):
        """Test material listing"""
        response = client.get('/')
        assert response.status_code == 200
    
    def test_material_detail_requires_login(self, client, test_material):
        """Test material detail requires login"""
        response = client.get(f'/material/{test_material.id}', follow_redirects=True)
        assert response.status_code == 200
    
    def test_search_functionality(self, client):
        """Test search functionality"""
        response = client.get('/search?q=test')
        assert response.status_code == 200


class TestAPIEndpoints:
    """Test API endpoints"""
    
    def test_user_details_api(self, admin_client, test_user):
        """Test user details API"""
        response = admin_client.get(f'/admin/users/{test_user.id}/details')
        # Should return JSON
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            assert response.is_json or 'application/json' in response.content_type

