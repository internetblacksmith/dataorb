import pytest
from flask import Flask
from app import app


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_health_endpoint(client):
    """Test the health check endpoint"""
    response = client.get('/api/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'healthy'
    assert 'timestamp' in data


def test_index_route(client):
    """Test that index route serves the React app"""
    response = client.get('/')
    assert response.status_code == 200


def test_available_metrics_endpoint(client):
    """Test available metrics endpoint"""
    response = client.get('/api/metrics/available')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, dict)
    # Check that some expected metrics are present
    assert 'events_24h' in data
    assert 'unique_users_24h' in data