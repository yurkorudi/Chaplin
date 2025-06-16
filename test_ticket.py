import pytest
from main import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_ticket_valid_json(client):
    response = client.post('/ticket', json={
        "seat": "A1",   
        "movie": "Transformers",
        "time": "2025-02-11T19:00:00"
    })
    assert response.status_code == 200
    assert response.get_json() == {"message": "Ticket booked successfully!", "status": "success"}

def test_ticket_missing_field(client):

    response = client.post('/ticket', json={"seat": "A1"})
    assert response.status_code == 400
    assert "error" in response.get_json()

def test_ticket_invalid_content_type(client):

    response = client.post('/ticket', data="seat=A1&movie=Transformers&time=2025-02-11T19:00:00",
                           headers={"Content-Type": "text/plain"})
    assert response.status_code == 415 
