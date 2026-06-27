from datetime import datetime, date
from sqlalchemy import func, and_
from app.extensions import db
from app.models.booking import Booking
from app.models.payment import Payment
from app.models.flight import Flight
from app.models.passenger import Passenger
from app.models.route import Route
from app.models.airport import Airport


def bookings_report(from_date, to_date):
    rows = db.session.query(
        func.date(Booking.booked_at).label('date'),
        func.count(Booking.id).label('total'),
        func.sum(func.if_(Booking.status == 'confirmed', 1, 0)).label('confirmed'),
        func.sum(func.if_(Booking.status == 'cancelled', 1, 0)).label('cancelled'),
    ).filter(
        func.date(Booking.booked_at).between(from_date, to_date)
    ).group_by(func.date(Booking.booked_at)).order_by('date').all()

    return [{'date': str(r.date), 'total': r.total, 'confirmed': r.confirmed, 'cancelled': r.cancelled}
            for r in rows]


def revenue_report(from_date, to_date, group_by='day'):
    trunc_map = {
        'day': func.date(Payment.paid_at),
        'month': func.date_format(Payment.paid_at, '%Y-%m'),
        'week': func.yearweek(Payment.paid_at),
    }
    trunc = trunc_map.get(group_by, func.date(Payment.paid_at))

    rows = db.session.query(
        trunc.label('period'),
        func.sum(Payment.amount).label('revenue'),
        func.count(Payment.id).label('transactions'),
    ).filter(
        Payment.status == 'completed',
        func.date(Payment.paid_at).between(from_date, to_date),
    ).group_by('period').order_by('period').all()

    return [{'period': str(r.period), 'revenue': float(r.revenue or 0), 'transactions': r.transactions}
            for r in rows]


def occupancy_report(from_date, to_date):
    rows = db.session.query(
        Flight.flight_number,
        Flight.departure_datetime,
        func.count(Booking.id).label('booked'),
    ).outerjoin(
        Booking, and_(Booking.flight_id == Flight.id, Booking.status.notin_(['cancelled', 'no_show']))
    ).filter(
        func.date(Flight.departure_datetime).between(from_date, to_date)
    ).group_by(Flight.id).all()

    result = []
    for r in rows:
        flight = Flight.query.filter_by(flight_number=r.flight_number).first()
        total = flight.aircraft.total_seats if flight and flight.aircraft else 0
        pct = round((r.booked / total) * 100, 1) if total else 0
        result.append({
            'flight_number': r.flight_number,
            'departure': r.departure_datetime.isoformat(),
            'booked': r.booked,
            'total_seats': total,
            'occupancy_pct': pct,
        })
    return result


def cancellations_report(from_date, to_date):
    rows = db.session.query(
        Booking.cancellation_reason,
        func.count(Booking.id).label('count'),
    ).filter(
        Booking.status == 'cancelled',
        func.date(Booking.cancelled_at).between(from_date, to_date),
    ).group_by(Booking.cancellation_reason).all()

    total = db.session.query(func.count(Booking.id)).filter(
        Booking.status == 'cancelled',
        func.date(Booking.cancelled_at).between(from_date, to_date),
    ).scalar()

    return {
        'total_cancellations': total,
        'breakdown': [{'reason': r.cancellation_reason or 'Not specified', 'count': r.count} for r in rows],
    }


def passenger_stats():
    total = Passenger.query.count()
    by_nationality = db.session.query(
        Passenger.nationality, func.count(Passenger.id).label('count')
    ).group_by(Passenger.nationality).order_by(func.count(Passenger.id).desc()).limit(10).all()

    top_ff = db.session.query(Passenger).order_by(Passenger.frequent_flyer_points.desc()).limit(10).all()

    return {
        'total_passengers': total,
        'top_nationalities': [{'nationality': r.nationality, 'count': r.count} for r in by_nationality],
        'top_frequent_flyers': [
            {'id': p.id, 'points': p.frequent_flyer_points, 'ffn': p.frequent_flyer_number}
            for p in top_ff
        ],
    }
