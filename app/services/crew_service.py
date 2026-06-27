from datetime import date
from app.extensions import db
from app.models.crew import CrewMember, FlightCrewAssignment
from app.models.flight import Flight
from app.models.audit_log import AuditLog


def create_crew_member(data):
    crew = CrewMember(
        user_id=data['user_id'],
        employee_id=data['employee_id'],
        crew_role=data['crew_role'],
        license_number=data.get('license_number'),
        certification_expiry=data.get('certification_expiry'),
        medical_expiry=data.get('medical_expiry'),
        hire_date=data.get('hire_date'),
    )
    db.session.add(crew)
    db.session.commit()
    return crew


def assign_crew_to_flight(flight_id, crew_member_id, role_on_flight, assigned_by):
    flight = Flight.query.get_or_404(flight_id)
    crew = CrewMember.query.get_or_404(crew_member_id)

    if not crew.is_certification_valid:
        raise ValueError(f'Crew member {crew.employee_id} has an expired certification.')
    if not crew.is_medical_valid:
        raise ValueError(f'Crew member {crew.employee_id} has an expired medical certificate.')

    # Check for scheduling conflict
    conflict = db.session.query(FlightCrewAssignment).join(Flight).filter(
        FlightCrewAssignment.crew_member_id == crew_member_id,
        Flight.departure_datetime < flight.arrival_datetime,
        Flight.arrival_datetime > flight.departure_datetime,
        Flight.id != flight_id,
        Flight.status.notin_(['cancelled']),
    ).first()
    if conflict:
        raise ValueError(f'Crew member is already assigned to another flight during this time.')

    existing = FlightCrewAssignment.query.filter_by(
        flight_id=flight_id, crew_member_id=crew_member_id
    ).first()
    if existing:
        raise ValueError('This crew member is already assigned to this flight.')

    assignment = FlightCrewAssignment(
        flight_id=flight_id,
        crew_member_id=crew_member_id,
        role_on_flight=role_on_flight,
        assigned_by=assigned_by,
    )
    db.session.add(assignment)

    log = AuditLog(user_id=assigned_by, action='CREATE', entity_type='flight_crew_assignment',
                   entity_id=assignment.id if assignment.id else None,
                   description=f'Crew {crew.employee_id} assigned to flight {flight.flight_number}')
    db.session.add(log)
    db.session.commit()

    from app.services.notification_service import send_notification
    send_notification(
        user_id=crew.user_id,
        notif_type='boarding_reminder',
        title='New Flight Assignment',
        message=f'You have been assigned to flight {flight.flight_number} '
                f'departing {flight.departure_datetime.strftime("%Y-%m-%d %H:%M")} UTC as {role_on_flight}.',
        send_email=True,
    )
    return assignment


def remove_crew_from_flight(flight_id, crew_member_id, removed_by):
    assignment = FlightCrewAssignment.query.filter_by(
        flight_id=flight_id, crew_member_id=crew_member_id
    ).first_or_404()

    db.session.delete(assignment)
    log = AuditLog(user_id=removed_by, action='DELETE', entity_type='flight_crew_assignment',
                   description=f'Crew member {crew_member_id} removed from flight {flight_id}')
    db.session.add(log)
    db.session.commit()
