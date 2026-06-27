import pytest
from app.models.seat import Seat


class TestBookingCreate:
    def test_create_booking_as_passenger(self, client, passenger_token, sample_flight, db_session):
        seat = Seat.query.filter_by(aircraft_id=sample_flight.aircraft_id).first()
        response = client.post('/api/v1/bookings', json={
            'flight_id': sample_flight.id,
            'seat_id': seat.id,
            'cabin_class': 'economy',
        }, headers={'Authorization': f'Bearer {passenger_token}'})
        assert response.status_code == 201
        data = response.json['data']
        assert data['status'] == 'pending'
        assert 'pnr_code' in data
        assert len(data['pnr_code']) == 6

    def test_create_booking_as_admin_forbidden(self, client, admin_token, sample_flight, db_session):
        seat = Seat.query.filter_by(aircraft_id=sample_flight.aircraft_id).first()
        response = client.post('/api/v1/bookings', json={
            'flight_id': sample_flight.id,
            'seat_id': seat.id,
            'cabin_class': 'economy',
        }, headers={'Authorization': f'Bearer {admin_token}'})
        assert response.status_code == 403

    def test_double_booking_same_seat(self, client, passenger_token, sample_flight, db_session):
        seat = Seat.query.filter_by(aircraft_id=sample_flight.aircraft_id).first()
        client.post('/api/v1/bookings', json={
            'flight_id': sample_flight.id,
            'seat_id': seat.id,
            'cabin_class': 'economy',
        }, headers={'Authorization': f'Bearer {passenger_token}'})

        response = client.post('/api/v1/bookings', json={
            'flight_id': sample_flight.id,
            'seat_id': seat.id,
            'cabin_class': 'economy',
        }, headers={'Authorization': f'Bearer {passenger_token}'})
        assert response.status_code == 409

    def test_create_booking_missing_fields(self, client, passenger_token):
        response = client.post('/api/v1/bookings', json={'flight_id': 1},
                               headers={'Authorization': f'Bearer {passenger_token}'})
        assert response.status_code == 422

    def test_create_booking_unauthenticated(self, client, sample_flight, db_session):
        seat = Seat.query.filter_by(aircraft_id=sample_flight.aircraft_id).first()
        response = client.post('/api/v1/bookings', json={
            'flight_id': sample_flight.id,
            'seat_id': seat.id,
            'cabin_class': 'economy',
        })
        assert response.status_code == 401


class TestMyBookings:
    def test_my_bookings_returns_own_only(self, client, passenger_token, sample_flight, db_session):
        seat = Seat.query.filter_by(aircraft_id=sample_flight.aircraft_id).first()
        client.post('/api/v1/bookings', json={
            'flight_id': sample_flight.id, 'seat_id': seat.id, 'cabin_class': 'economy',
        }, headers={'Authorization': f'Bearer {passenger_token}'})

        response = client.get('/api/v1/bookings/my', headers={'Authorization': f'Bearer {passenger_token}'})
        assert response.status_code == 200
        assert len(response.json['data']) >= 1

    def test_my_bookings_admin_forbidden(self, client, admin_token):
        response = client.get('/api/v1/bookings/my', headers={'Authorization': f'Bearer {admin_token}'})
        assert response.status_code == 404  # no passenger profile for admin


class TestBookingCancel:
    def test_cancel_own_booking(self, client, passenger_token, sample_flight, db_session):
        seat = Seat.query.filter_by(aircraft_id=sample_flight.aircraft_id).first()
        create_resp = client.post('/api/v1/bookings', json={
            'flight_id': sample_flight.id, 'seat_id': seat.id, 'cabin_class': 'economy',
        }, headers={'Authorization': f'Bearer {passenger_token}'})
        booking_id = create_resp.json['data']['id']

        cancel_resp = client.patch(
            f'/api/v1/bookings/{booking_id}/cancel',
            json={'reason': 'Changed plans'},
            headers={'Authorization': f'Bearer {passenger_token}'},
        )
        assert cancel_resp.status_code == 200
        assert cancel_resp.json['data']['status'] == 'cancelled'

    def test_cancel_by_pnr_lookup(self, client, passenger_token, sample_flight, db_session):
        seat = Seat.query.filter_by(aircraft_id=sample_flight.aircraft_id).first()
        create_resp = client.post('/api/v1/bookings', json={
            'flight_id': sample_flight.id, 'seat_id': seat.id, 'cabin_class': 'economy',
        }, headers={'Authorization': f'Bearer {passenger_token}'})
        pnr = create_resp.json['data']['pnr_code']

        pnr_resp = client.get(f'/api/v1/bookings/pnr/{pnr}')
        assert pnr_resp.status_code == 200
        assert pnr_resp.json['data']['pnr_code'] == pnr
