import pytest
from datetime import datetime, timedelta


class TestFlightSearch:
    def test_list_flights_no_filter(self, client, sample_flight):
        response = client.get('/api/v1/flights')
        assert response.status_code == 200
        assert response.json['success'] is True
        assert isinstance(response.json['data'], list)

    def test_search_flights_by_route(self, client, sample_flight):
        dep_date = (datetime.utcnow() + timedelta(days=7)).strftime('%Y-%m-%d')
        response = client.get(f'/api/v1/flights?origin=NBO&destination=DAR&departure_date={dep_date}')
        assert response.status_code == 200
        flights = response.json['data']
        assert len(flights) >= 1
        assert flights[0]['flight_number'] == 'KQ101'

    def test_search_invalid_date(self, client):
        response = client.get('/api/v1/flights?origin=NBO&destination=DAR&departure_date=not-a-date')
        assert response.status_code == 400


class TestFlightCRUD:
    def test_get_flight_by_id(self, client, sample_flight):
        response = client.get(f'/api/v1/flights/{sample_flight.id}')
        assert response.status_code == 200
        assert response.json['data']['flight_number'] == 'KQ101'

    def test_get_nonexistent_flight(self, client):
        response = client.get('/api/v1/flights/99999')
        assert response.status_code == 404

    def test_create_flight_as_admin(self, client, admin_token, sample_flight):
        dep = (datetime.utcnow() + timedelta(days=14)).isoformat()
        arr = (datetime.utcnow() + timedelta(days=14, hours=2)).isoformat()
        response = client.post('/api/v1/flights', json={
            'flight_number': 'KQ202',
            'route_id': sample_flight.route_id,
            'aircraft_id': sample_flight.aircraft_id,
            'departure_datetime': dep,
            'arrival_datetime': arr,
            'economy_price': 200.00,
        }, headers={'Authorization': f'Bearer {admin_token}'})
        assert response.status_code == 201
        assert response.json['data']['flight_number'] == 'KQ202'

    def test_create_flight_as_passenger_forbidden(self, client, passenger_token, sample_flight):
        dep = (datetime.utcnow() + timedelta(days=14)).isoformat()
        arr = (datetime.utcnow() + timedelta(days=14, hours=2)).isoformat()
        response = client.post('/api/v1/flights', json={
            'flight_number': 'KQ303',
            'route_id': sample_flight.route_id,
            'aircraft_id': sample_flight.aircraft_id,
            'departure_datetime': dep,
            'arrival_datetime': arr,
            'economy_price': 150.00,
        }, headers={'Authorization': f'Bearer {passenger_token}'})
        assert response.status_code == 403

    def test_create_flight_unauthenticated(self, client):
        response = client.post('/api/v1/flights', json={'flight_number': 'XX1'})
        assert response.status_code == 401


class TestFlightStatus:
    def test_update_status_to_delayed(self, client, admin_token, sample_flight):
        response = client.patch(
            f'/api/v1/flights/{sample_flight.id}/status',
            json={'status': 'delayed', 'delay_minutes': 30, 'delay_reason': 'Weather'},
            headers={'Authorization': f'Bearer {admin_token}'},
        )
        assert response.status_code == 200
        assert response.json['data']['status'] == 'delayed'
        assert response.json['data']['delay_minutes'] == 30

    def test_update_status_invalid(self, client, admin_token, sample_flight):
        response = client.patch(
            f'/api/v1/flights/{sample_flight.id}/status',
            json={'status': 'flying'},
            headers={'Authorization': f'Bearer {admin_token}'},
        )
        assert response.status_code == 422


class TestSeatAvailability:
    def test_get_seats(self, client, sample_flight):
        response = client.get(f'/api/v1/flights/{sample_flight.id}/seats')
        assert response.status_code == 200
        seats = response.json['data']
        assert isinstance(seats, list)
        assert all('is_available' in s for s in seats)
