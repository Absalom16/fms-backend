import pytest
from app import create_app
from app.extensions import db as _db
from app.models.user import User
from app.models.passenger import Passenger
from app.models.airport import Airport
from app.models.aircraft import Aircraft
from app.models.seat import Seat
from app.models.route import Route
from app.models.flight import Flight


@pytest.fixture(scope='session')
def app():
    app = create_app('testing')
    with app.app_context():
        _db.create_all()
        yield app
        _db.drop_all()


@pytest.fixture(scope='session')
def client(app):
    return app.test_client()


@pytest.fixture(scope='function', autouse=True)
def db_session(app):
    """Wrap each test in a transaction that is rolled back after."""
    with app.app_context():
        connection = _db.engine.connect()
        transaction = connection.begin()
        _db.session.bind = connection
        yield _db
        _db.session.remove()
        transaction.rollback()
        connection.close()


@pytest.fixture
def admin_user(db_session):
    user = User(email='admin@test.com', first_name='Admin', last_name='Test', role='admin')
    user.set_password('Admin@1234')
    db_session.session.add(user)
    db_session.session.commit()
    return user


@pytest.fixture
def passenger_user(db_session):
    user = User(email='passenger@test.com', first_name='Jane', last_name='Doe', role='passenger')
    user.set_password('Pass@1234')
    db_session.session.add(user)
    db_session.session.flush()
    profile = Passenger(user_id=user.id)
    db_session.session.add(profile)
    db_session.session.commit()
    return user


@pytest.fixture
def admin_token(client, admin_user):
    response = client.post('/api/v1/auth/login', json={
        'email': 'admin@test.com',
        'password': 'Admin@1234',
    })
    return response.json['data']['access_token']


@pytest.fixture
def passenger_token(client, passenger_user):
    response = client.post('/api/v1/auth/login', json={
        'email': 'passenger@test.com',
        'password': 'Pass@1234',
    })
    return response.json['data']['access_token']


@pytest.fixture
def sample_flight(db_session, admin_user):
    origin = Airport(iata_code='NBO', name='Jomo Kenyatta', city='Nairobi', country='Kenya', timezone='Africa/Nairobi')
    dest = Airport(iata_code='DAR', name='Julius Nyerere', city='Dar es Salaam', country='Tanzania', timezone='Africa/Dar_es_Salaam')
    db_session.session.add_all([origin, dest])
    db_session.session.flush()

    route = Route(origin_airport_id=origin.id, destination_airport_id=dest.id, distance_km=650, estimated_duration_minutes=90)
    db_session.session.add(route)
    db_session.session.flush()

    aircraft = Aircraft(registration_number='5Y-TEST', model='Boeing 737', economy_seats=120, business_seats=20)
    db_session.session.add(aircraft)
    db_session.session.flush()

    from datetime import datetime, timedelta
    flight = Flight(
        flight_number='KQ101',
        route_id=route.id,
        aircraft_id=aircraft.id,
        departure_datetime=datetime.utcnow() + timedelta(days=7),
        arrival_datetime=datetime.utcnow() + timedelta(days=7, hours=2),
        economy_price=150.00,
        business_price=450.00,
        created_by=admin_user.id,
    )
    db_session.session.add(flight)

    seat = Seat(aircraft_id=aircraft.id, seat_number='14A', seat_class='economy', is_window=True)
    db_session.session.add(seat)
    db_session.session.commit()
    return flight
