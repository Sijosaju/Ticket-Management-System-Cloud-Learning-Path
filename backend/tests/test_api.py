import os, sys
import pytest
from datetime import date, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app import create_app
from app.models import db, Event, TicketType, User

@pytest.fixture
def app():
    application = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:", "JWT_SECRET_KEY": "test"})
    with application.app_context():
        db.create_all()
        db.session.commit()
    yield application

@pytest.fixture
def client(app): return app.test_client()
def login(client, email, password): return client.post('/api/auth/login', json={'email':email,'password':password}).get_json()['access_token']
def headers(token): return {'Authorization':f'Bearer {token}'}
def event_data(): return {'title':'Music Night','description':'A live show','category':'Music','location':'Hall A','event_date':'2030-01-20','event_time':'19:30'}

def test_registration_and_login(client):
    assert client.post('/api/auth/register', json={'name':'Sam','email':'sam@test.com','password':'secret1'}).status_code == 201
    assert client.post('/api/auth/login', json={'email':'sam@test.com','password':'secret1'}).status_code == 200

def test_event_retrieval_and_admin_creation(app, client):
    client.post('/api/auth/register', json={'name':'Admin','email':'admin@example.com','password':'admin123'})
    with app.app_context():
        User.query.filter_by(email='admin@example.com').first().role='admin'; db.session.commit()
    admin_token = login(client, 'admin@example.com', 'admin123')
    no_auth = client.post('/api/events', json=event_data()); assert no_auth.status_code == 401
    assert client.post('/api/events', json=event_data(), headers=headers(admin_token)).status_code == 201
    assert len(client.get('/api/events').get_json()['events']) == 1

def test_booking_availability_and_cancellation(app, client):
    client.post('/api/auth/register', json={'name':'Sam','email':'sam@test.com','password':'secret1'})
    token=login(client,'sam@test.com','secret1')
    with app.app_context():
        event=Event(**{**event_data(), 'event_date':date(2030,1,20), 'event_time':time(19,30)}); db.session.add(event); db.session.flush()
        ticket=TicketType(event_id=event.id,name='VIP',price=50,total_quantity=5,available_quantity=5); db.session.add(ticket); db.session.commit(); tid=ticket.id
    response=client.post('/api/bookings',json={'event_id':1,'items':[{'ticket_type_id':tid,'quantity':3}]},headers=headers(token)); assert response.status_code==201
    bookings = client.get('/api/bookings', headers=headers(token))
    assert bookings.status_code == 200
    assert len(bookings.get_json()['bookings']) == 1
    assert client.post('/api/bookings',json={'event_id':1,'items':[{'ticket_type_id':tid,'quantity':3}]},headers=headers(token)).status_code==409
    booking_id=response.get_json()['booking']['id']; assert client.post(f'/api/bookings/{booking_id}/cancel',headers=headers(token)).status_code==200
    with app.app_context(): assert db.session.get(TicketType,tid).available_quantity==5
