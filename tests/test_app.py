# Import sys module for modifying Python's runtime environment
import sys
# Import os module for interacting with the operating system
import os

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the Flask app instance from the main app file
# Import pytest for writing and running tests
import pytest

@pytest.fixture
def client(app):
    """A test client for the app."""
    with app.test_client() as client:
        yield client

def test_home(client):
    """Test the home route."""
    response = client.get('/home')
    assert response.status_code == 200
    # assert response.json == {"message": "Hello, Flask!"}

def test_add_cinema(client, app):
    import re
    from models import User, Cinema
    with app.app_context():
        admin_id = User.query.filter_by(login='admin').one().id
    # Establish an authenticated test session; login security is tested separately.
    with client.session_transaction() as state:
        state['user_id'] = admin_id
        state['user'] = 'admin'
    response = client.get('/admin/cinema/new/')
    token = re.search(rb'name="csrf-token" content="([^"]+)"', response.data).group(1).decode()
    response = client.post('/admin/cinema/new/', data={
        'name': 'Інтеграційний кінотеатр', 'city': 'Тестове місто',
        'location': 'Демонстраційна адреса', 'csrf_token': token,
    })
    assert response.status_code == 302
    with app.app_context():
        assert Cinema.query.filter_by(name='Інтеграційний кінотеатр').count() == 1
