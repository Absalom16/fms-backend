from datetime import date, datetime, timedelta
from flask import Blueprint, request
from sqlalchemy import func
from app.extensions import db
from app.services.report_service import (
    bookings_report, revenue_report, occupancy_report,
    cancellations_report, passenger_stats,
)
from app.utils.responses import success_response, error_response
from app.utils.decorators import roles_required

reports_bp = Blueprint('reports', __name__)


@reports_bp.get('/summary')
@roles_required('admin', 'manager')
def summary():
    from app.models.booking import Booking
    from app.models.flight import Flight
    from app.models.passenger import Passenger
    from app.models.payment import Payment

    now = datetime.utcnow()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    total_bookings = Booking.query.count()
    total_revenue = db.session.query(func.coalesce(func.sum(Payment.amount), 0)).filter(
        Payment.status == 'completed'
    ).scalar()
    active_flights = Flight.query.filter(
        Flight.status.in_(['scheduled', 'boarding', 'departed']),
        Flight.departure_datetime >= now,
    ).count()
    total_passengers = Passenger.query.count()
    monthly_revenue = db.session.query(func.coalesce(func.sum(Payment.amount), 0)).filter(
        Payment.status == 'completed',
        Payment.paid_at >= month_start,
    ).scalar()
    monthly_bookings = Booking.query.filter(Booking.booked_at >= month_start).count()
    confirmed_bookings = Booking.query.filter(Booking.status == 'confirmed').count()
    cancelled_bookings = Booking.query.filter(Booking.status == 'cancelled').count()

    return success_response({
        'total_bookings': total_bookings,
        'total_revenue': float(total_revenue or 0),
        'active_flights': active_flights,
        'total_passengers': total_passengers,
        'monthly_revenue': float(monthly_revenue or 0),
        'monthly_bookings': monthly_bookings,
        'confirmed_bookings': confirmed_bookings,
        'cancelled_bookings': cancelled_bookings,
    })


def _parse_date_range():
    # Accept both start_date/end_date (frontend) and from/to (legacy)
    from_str = request.args.get('start_date') or request.args.get('from', str(date.today().replace(day=1)))
    to_str   = request.args.get('end_date')   or request.args.get('to',   str(date.today()))
    try:
        return date.fromisoformat(from_str), date.fromisoformat(to_str)
    except ValueError:
        return None, None


PERIOD_MAP = {'daily': 'day', 'weekly': 'week', 'monthly': 'month'}


@reports_bp.get('/bookings')
@roles_required('admin', 'manager')
def bookings():
    from_date, to_date = _parse_date_range()
    if not from_date:
        return error_response('INVALID_DATE', 'Use YYYY-MM-DD for date parameters.', 400)
    return success_response(bookings_report(from_date, to_date))


@reports_bp.get('/revenue')
@roles_required('admin', 'manager')
def revenue():
    from_date, to_date = _parse_date_range()
    if not from_date:
        return error_response('INVALID_DATE', 'Use YYYY-MM-DD for date parameters.', 400)
    raw = request.args.get('period') or request.args.get('group_by', 'daily')
    group_by = PERIOD_MAP.get(raw, raw)
    if group_by not in ('day', 'week', 'month'):
        group_by = 'day'
    return success_response(revenue_report(from_date, to_date, group_by))


@reports_bp.get('/occupancy')
@roles_required('admin', 'manager')
def occupancy():
    from_date, to_date = _parse_date_range()
    if not from_date:
        return error_response('INVALID_DATE', 'Use YYYY-MM-DD for from/to parameters.', 400)
    return success_response(occupancy_report(from_date, to_date))


@reports_bp.get('/cancellations')
@roles_required('admin', 'manager')
def cancellations():
    from_date, to_date = _parse_date_range()
    if not from_date:
        return error_response('INVALID_DATE', 'Use YYYY-MM-DD for from/to parameters.', 400)
    return success_response(cancellations_report(from_date, to_date))


@reports_bp.get('/passengers')
@roles_required('admin', 'manager')
def passengers():
    return success_response(passenger_stats())
