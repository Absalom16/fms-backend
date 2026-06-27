import pytest


class TestRegister:
    def test_register_passenger_success(self, client):
        response = client.post('/api/v1/auth/register', json={
            'email': 'new@test.com',
            'password': 'NewPass@1234',
            'first_name': 'New',
            'last_name': 'User',
            'role': 'passenger',
        })
        assert response.status_code == 201
        data = response.json
        assert data['success'] is True
        assert 'access_token' in data['data']
        assert data['data']['user']['role'] == 'passenger'

    def test_register_duplicate_email(self, client, passenger_user):
        response = client.post('/api/v1/auth/register', json={
            'email': 'passenger@test.com',
            'password': 'Pass@1234',
            'first_name': 'Dup',
            'last_name': 'User',
            'role': 'passenger',
        })
        assert response.status_code == 409

    def test_register_missing_fields(self, client):
        response = client.post('/api/v1/auth/register', json={'email': 'x@test.com'})
        assert response.status_code == 422

    def test_register_weak_password(self, client):
        response = client.post('/api/v1/auth/register', json={
            'email': 'weak@test.com',
            'password': 'short',
            'first_name': 'Weak',
            'last_name': 'Pass',
            'role': 'passenger',
        })
        assert response.status_code == 422

    def test_register_invalid_role(self, client):
        response = client.post('/api/v1/auth/register', json={
            'email': 'role@test.com',
            'password': 'RolePass@1234',
            'first_name': 'Role',
            'last_name': 'Test',
            'role': 'superuser',
        })
        assert response.status_code == 422


class TestLogin:
    def test_login_success(self, client, admin_user):
        response = client.post('/api/v1/auth/login', json={
            'email': 'admin@test.com',
            'password': 'Admin@1234',
        })
        assert response.status_code == 200
        data = response.json
        assert data['success'] is True
        assert 'access_token' in data['data']
        assert 'refresh_token' in data['data']

    def test_login_wrong_password(self, client, admin_user):
        response = client.post('/api/v1/auth/login', json={
            'email': 'admin@test.com',
            'password': 'wrong_password',
        })
        assert response.status_code == 401

    def test_login_unknown_email(self, client):
        response = client.post('/api/v1/auth/login', json={
            'email': 'nobody@test.com',
            'password': 'SomePass@1',
        })
        assert response.status_code == 401

    def test_login_missing_body(self, client):
        response = client.post('/api/v1/auth/login', json={})
        assert response.status_code == 400


class TestMe:
    def test_get_me_authenticated(self, client, admin_token):
        response = client.get('/api/v1/auth/me', headers={'Authorization': f'Bearer {admin_token}'})
        assert response.status_code == 200
        assert response.json['data']['email'] == 'admin@test.com'

    def test_get_me_unauthenticated(self, client):
        response = client.get('/api/v1/auth/me')
        assert response.status_code == 401


class TestLogout:
    def test_logout_success(self, client, admin_token):
        response = client.post('/api/v1/auth/logout', headers={'Authorization': f'Bearer {admin_token}'})
        assert response.status_code == 200

    def test_access_after_logout(self, client, admin_user):
        login_resp = client.post('/api/v1/auth/login', json={
            'email': 'admin@test.com', 'password': 'Admin@1234'
        })
        token = login_resp.json['data']['access_token']
        client.post('/api/v1/auth/logout', headers={'Authorization': f'Bearer {token}'})
        me_resp = client.get('/api/v1/auth/me', headers={'Authorization': f'Bearer {token}'})
        assert me_resp.status_code == 401
