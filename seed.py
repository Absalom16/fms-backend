"""
Seed script — run once on first startup to populate the database.
Idempotent: checks for existing data before inserting.
"""
import os
import sys
import random
import string
from datetime import datetime, date, timedelta

# Flask app context must be available before importing models
from app import create_app
from app.extensions import db

app = create_app(os.environ.get('FLASK_ENV', 'production'))


def _pnr():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))


def _ticket_number():
    return 'TKT' + ''.join(random.choices(string.digits, k=10))


def _barcode():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=24))


def seed_users():
    from app.models.user import User
    from app.models.passenger import Passenger
    from app.models.crew import CrewMember

    if User.query.count() > 0:
        print("  [skip] users already seeded")
        return

    users_data = [
        dict(email='admin@airline.com',     password='Admin@1234',     first_name='Alice',  last_name='Kamau',     phone='+254700000001', role='admin'),
        dict(email='manager@airline.com',   password='Manager@1234',   first_name='Brian',  last_name='Oduya',     phone='+254700000002', role='manager'),
        dict(email='pilot@airline.com',     password='Pilot@1234',     first_name='Captain',last_name='Mwangi',    phone='+254700000003', role='crew'),
        dict(email='copilot@airline.com',   password='CoPilot@1234',   first_name='James',  last_name='Otieno',    phone='+254700000004', role='crew'),
        dict(email='purser@airline.com',    password='Purser@1234',    first_name='Grace',  last_name='Wanjiku',   phone='+254700000005', role='crew'),
        dict(email='crew1@airline.com',     password='Crew@1234',      first_name='David',  last_name='Ndung\'u',  phone='+254700000006', role='crew'),
        dict(email='crew2@airline.com',     password='Crew@1234',      first_name='Faith',  last_name='Achieng',   phone='+254700000007', role='crew'),
        dict(email='passenger@airline.com', password='Passenger@1234', first_name='John',   last_name='Doe',       phone='+254700000010', role='passenger'),
        dict(email='jane@airline.com',      password='Passenger@1234', first_name='Jane',   last_name='Smith',     phone='+254700000011', role='passenger'),
        dict(email='samuel@airline.com',    password='Passenger@1234', first_name='Samuel', last_name='Mutua',     phone='+254700000012', role='passenger'),
    ]

    created = {}
    for u in users_data:
        user = User(
            email=u['email'], first_name=u['first_name'],
            last_name=u['last_name'], phone=u['phone'], role=u['role']
        )
        user.set_password(u['password'])
        db.session.add(user)
        db.session.flush()
        created[u['email']] = user

    # Passenger profiles
    passengers = ['passenger@airline.com', 'jane@airline.com', 'samuel@airline.com']
    p_details = [
        dict(nationality='Kenyan',    gender='male',   dob=date(1990, 3, 15), passport='A12345678', expiry=date(2028, 3, 14)),
        dict(nationality='American',  gender='female', dob=date(1995, 7, 22), passport='B87654321', expiry=date(2029, 7, 21)),
        dict(nationality='Kenyan',    gender='male',   dob=date(1988, 11, 5), passport='C11223344', expiry=date(2027, 11, 4)),
    ]
    for email, details in zip(passengers, p_details):
        p = Passenger(user_id=created[email].id, nationality=details['nationality'],
                      gender=details['gender'], date_of_birth=details['dob'],
                      travel_document_expiry=details['expiry'],
                      frequent_flyer_points=random.randint(500, 12000))
        p.passport_number = details['passport']
        db.session.add(p)

    # Crew profiles
    crew_data = [
        dict(email='pilot@airline.com',  emp='EMP001', role='pilot',            license='PIL-KE-001', cert=date(2026, 6, 1), medical=date(2026, 3, 1), hire=date(2015, 1, 10)),
        dict(email='copilot@airline.com',emp='EMP002', role='co_pilot',         license='PIL-KE-002', cert=date(2026, 8, 1), medical=date(2026, 5, 1), hire=date(2018, 3, 20)),
        dict(email='purser@airline.com', emp='EMP003', role='purser',           license=None,          cert=date(2026, 9, 1), medical=date(2026, 6, 1), hire=date(2017, 6, 15)),
        dict(email='crew1@airline.com',  emp='EMP004', role='flight_attendant', license=None,          cert=date(2026, 7, 1), medical=date(2026, 4, 1), hire=date(2019, 8, 1)),
        dict(email='crew2@airline.com',  emp='EMP005', role='flight_attendant', license=None,          cert=date(2027, 1, 1), medical=date(2026, 9, 1), hire=date(2020, 2, 14)),
    ]
    for c in crew_data:
        crew = CrewMember(
            user_id=created[c['email']].id, employee_id=c['emp'],
            crew_role=c['role'], license_number=c['license'],
            certification_expiry=c['cert'], medical_expiry=c['medical'],
            hire_date=c['hire'], status='active'
        )
        db.session.add(crew)

    db.session.commit()
    print(f"  [ok] seeded {len(users_data)} users, {len(passengers)} passenger profiles, {len(crew_data)} crew members")


def seed_airports():
    from app.models.airport import Airport

    if Airport.query.count() > 0:
        print("  [skip] airports already seeded")
        return

    airports = [
        dict(iata_code='NBO', icao_code='HKJK', name='Jomo Kenyatta International Airport', city='Nairobi',        country='Kenya',        timezone='Africa/Nairobi',    latitude=-1.319167,  longitude=36.927778),
        dict(iata_code='DAR', icao_code='HTDA', name='Julius Nyerere International Airport', city='Dar es Salaam', country='Tanzania',      timezone='Africa/Dar_es_Salaam', latitude=-6.878056, longitude=39.202500),
        dict(iata_code='ADD', icao_code='HAAB', name='Addis Ababa Bole International Airport', city='Addis Ababa', country='Ethiopia',      timezone='Africa/Addis_Ababa', latitude=8.977778,  longitude=38.799444),
        dict(iata_code='LOS', icao_code='DNMM', name='Murtala Muhammed International Airport', city='Lagos',       country='Nigeria',       timezone='Africa/Lagos',      latitude=6.577222,   longitude=3.321111),
        dict(iata_code='ACC', icao_code='DGAA', name='Kotoka International Airport',          city='Accra',        country='Ghana',         timezone='Africa/Accra',      latitude=5.605186,   longitude=-0.166786),
        dict(iata_code='JNB', icao_code='FAOR', name='O.R. Tambo International Airport',      city='Johannesburg', country='South Africa',  timezone='Africa/Johannesburg',latitude=-26.133694, longitude=28.242317),
        dict(iata_code='CPT', icao_code='FACT', name='Cape Town International Airport',       city='Cape Town',    country='South Africa',  timezone='Africa/Johannesburg',latitude=-33.964806, longitude=18.601667),
        dict(iata_code='CMN', icao_code='GMMN', name='Mohammed V International Airport',      city='Casablanca',   country='Morocco',       timezone='Africa/Casablanca', latitude=33.367500,  longitude=-7.589722),
        dict(iata_code='DXB', icao_code='OMDB', name='Dubai International Airport',           city='Dubai',        country='UAE',           timezone='Asia/Dubai',        latitude=25.252778,  longitude=55.364444),
        dict(iata_code='LHR', icao_code='EGLL', name='London Heathrow Airport',               city='London',       country='United Kingdom',timezone='Europe/London',     latitude=51.477500,  longitude=-0.461389),
        dict(iata_code='CDG', icao_code='LFPG', name='Charles de Gaulle Airport',             city='Paris',        country='France',        timezone='Europe/Paris',      latitude=49.012779,  longitude=2.550000),
        dict(iata_code='EBB', icao_code='HUEN', name='Entebbe International Airport',         city='Kampala',      country='Uganda',        timezone='Africa/Kampala',    latitude=0.042386,   longitude=32.443503),
        dict(iata_code='MBA', icao_code='HKMO', name='Moi International Airport',             city='Mombasa',      country='Kenya',         timezone='Africa/Nairobi',    latitude=-4.034833,  longitude=39.594183),
        dict(iata_code='KGL', icao_code='HRYR', name='Kigali International Airport',          city='Kigali',       country='Rwanda',        timezone='Africa/Kigali',     latitude=-1.968628,  longitude=30.139444),
    ]

    for a in airports:
        db.session.add(Airport(**a))

    db.session.commit()
    print(f"  [ok] seeded {len(airports)} airports")


def seed_aircraft():
    from app.models.aircraft import Aircraft
    from app.models.seat import Seat

    if Aircraft.query.count() > 0:
        print("  [skip] aircraft already seeded")
        return

    fleet = [
        dict(reg='5Y-KZA', model='Boeing 737-800',    manufacturer='Boeing',  economy=144, business=12, first=0),
        dict(reg='5Y-KZB', model='Boeing 737-800',    manufacturer='Boeing',  economy=144, business=12, first=0),
        dict(reg='5Y-KZC', model='Airbus A320',       manufacturer='Airbus',  economy=150, business=12, first=0),
        dict(reg='5Y-KZD', model='Boeing 777-300ER',  manufacturer='Boeing',  economy=200, business=42, first=8),
        dict(reg='5Y-KZE', model='Bombardier CRJ-900',manufacturer='Bombardier', economy=74, business=12, first=0),
        dict(reg='5Y-KZF', model='Airbus A350-900',   manufacturer='Airbus',  economy=253, business=42, first=10),
    ]

    for f in fleet:
        ac = Aircraft(
            registration_number=f['reg'], model=f['model'], manufacturer=f['manufacturer'],
            economy_seats=f['economy'], business_seats=f['business'], first_class_seats=f['first'],
            status='active'
        )
        db.session.add(ac)
        db.session.flush()
        _generate_seats(ac)

    db.session.commit()
    print(f"  [ok] seeded {len(fleet)} aircraft with seats")


def _generate_seats(aircraft):
    from app.models.seat import Seat

    seats = []

    # First class: rows 1-N, seats A-C (2-2 config)
    fc_rows = aircraft.first_class_seats // 4
    for row in range(1, fc_rows + 1):
        for col, letter in enumerate(['A', 'B', 'C', 'D']):
            seats.append(Seat(
                aircraft_id=aircraft.id,
                seat_number=f'{row}{letter}',
                seat_class='first',
                is_window=(letter in ('A', 'D')),
                is_aisle=(letter in ('B', 'C')),
                is_extra_legroom=(row == 1)
            ))

    # Business class: rows 10-N, seats A-D (2-2 config)
    biz_rows = aircraft.business_seats // 4
    start_row = (fc_rows or 0) + 10
    for row in range(start_row, start_row + biz_rows):
        for col, letter in enumerate(['A', 'B', 'C', 'D']):
            seats.append(Seat(
                aircraft_id=aircraft.id,
                seat_number=f'{row}{letter}',
                seat_class='business',
                is_window=(letter in ('A', 'D')),
                is_aisle=(letter in ('B', 'C')),
                is_extra_legroom=(row == start_row)
            ))

    # Economy: rows 20+, seats A-F (3-3 config)
    eco_rows = aircraft.economy_seats // 6
    eco_start = (fc_rows or 0) + biz_rows + 20
    for row in range(eco_start, eco_start + eco_rows):
        for col, letter in enumerate(['A', 'B', 'C', 'D', 'E', 'F']):
            seats.append(Seat(
                aircraft_id=aircraft.id,
                seat_number=f'{row}{letter}',
                seat_class='economy',
                is_window=(letter in ('A', 'F')),
                is_aisle=(letter in ('C', 'D')),
                is_extra_legroom=(row == eco_start)
            ))

    for s in seats:
        db.session.add(s)


def seed_routes():
    from app.models.airport import Airport
    from app.models.route import Route

    if Route.query.count() > 0:
        print("  [skip] routes already seeded")
        return

    # Map IATA → id
    airports = {a.iata_code: a.id for a in Airport.query.all()}

    route_pairs = [
        ('NBO', 'DAR', 880,   120),
        ('DAR', 'NBO', 880,   120),
        ('NBO', 'ADD', 1160,  165),
        ('ADD', 'NBO', 1160,  165),
        ('NBO', 'LOS', 3860,  330),
        ('LOS', 'NBO', 3860,  330),
        ('NBO', 'JNB', 3800,  330),
        ('JNB', 'NBO', 3800,  330),
        ('NBO', 'DXB', 3420,  280),
        ('DXB', 'NBO', 3420,  280),
        ('NBO', 'LHR', 6820,  520),
        ('LHR', 'NBO', 6820,  520),
        ('LOS', 'ACC', 480,    80),
        ('ACC', 'LOS', 480,    80),
        ('JNB', 'CPT', 1390,  110),
        ('CPT', 'JNB', 1390,  110),
        ('ADD', 'DXB', 2850,  235),
        ('DXB', 'ADD', 2850,  235),
        ('NBO', 'EBB', 515,    70),
        ('EBB', 'NBO', 515,    70),
        ('NBO', 'MBA', 470,    60),
        ('MBA', 'NBO', 470,    60),
        ('NBO', 'KGL', 780,   100),
        ('KGL', 'NBO', 780,   100),
        ('JNB', 'LHR', 9070,  660),
        ('LHR', 'JNB', 9070,  660),
    ]

    for orig, dest, dist, dur in route_pairs:
        if orig in airports and dest in airports:
            db.session.add(Route(
                origin_airport_id=airports[orig],
                destination_airport_id=airports[dest],
                distance_km=dist,
                estimated_duration_minutes=dur
            ))

    db.session.commit()
    print(f"  [ok] seeded {len(route_pairs)} routes")


def seed_flights():
    from app.models.flight import Flight
    from app.models.route import Route
    from app.models.aircraft import Aircraft
    from app.models.user import User

    if Flight.query.count() > 0:
        print("  [skip] flights already seeded")
        return

    routes   = {(r.origin_airport_id, r.destination_airport_id): r for r in Route.query.all()}
    aircraft = Aircraft.query.all()
    admin    = User.query.filter_by(role='admin').first()

    from app.models.airport import Airport
    ap = {a.iata_code: a.id for a in Airport.query.all()}

    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    # (origin, dest, times, economy_price, business_price, first_price, gate)
    schedules = [
        # NBO ↔ DAR — short-haul
        ('NBO','DAR', [(6,0,  8,0 ), (10,30, 12,30), (14,0,  16,0 ), (18,0,  20,0 )],  120,  280,  None, 'A1'),
        ('DAR','NBO', [(7,0,  9,0 ), (11,30, 13,30), (15,0,  17,0 ), (19,0,  21,0 )],  120,  280,  None, 'B2'),
        # NBO ↔ ADD — medium
        ('NBO','ADD', [(7,0,  9,45), (13,0,  15,45), (19,0,  21,45)],                   180,  420,  None, 'A3'),
        ('ADD','NBO', [(6,0,  8,45), (12,0,  14,45), (18,0,  20,45)],                   180,  420,  None, 'C1'),
        # NBO ↔ LOS — long-haul
        ('NBO','LOS', [(8,0,  13,30), (22,0,  3,30)],                                   320,  780,  None, 'B1'),
        ('LOS','NBO', [(9,0,  14,30), (23,0,  4,30)],                                   320,  780,  None, 'D2'),
        # NBO ↔ JNB — long-haul
        ('NBO','JNB', [(9,0,  14,30), (21,0,  2,30)],                                   350,  850,  None, 'B3'),
        ('JNB','NBO', [(8,0,  13,30), (20,0,  1,30)],                                   350,  850,  None, 'E1'),
        # NBO ↔ DXB — international
        ('NBO','DXB', [(1,0,  5,40), (11,0,  15,40), (23,30, 4,10)],                    410,  980, 1850, 'C2'),
        ('DXB','NBO', [(2,0,  6,40), (12,0,  16,40), (20,0,  0,40)],                    410,  980, 1850, 'F3'),
        # NBO ↔ LHR — ultra long-haul
        ('NBO','LHR', [(22,0, 6,40), (10,0,  18,40)],                                   680, 1650, 3200, 'C3'),
        ('LHR','NBO', [(21,0, 5,40), (11,0,  19,40)],                                   680, 1650, 3200, 'T5A'),
        # LOS ↔ ACC — short
        ('LOS','ACC', [(7,0,  8,20), (13,0,  14,20), (17,0,  18,20)],                    90,  210,  None, 'D1'),
        ('ACC','LOS', [(8,0,  9,20), (14,0,  15,20), (18,0,  19,20)],                    90,  210,  None, 'G1'),
        # JNB ↔ CPT — domestic
        ('JNB','CPT', [(6,0,  7,50), (9,0,  10,50), (13,0,  14,50), (17,0,  18,50), (20,0,  21,50)], 80, 180, None, 'A2'),
        ('CPT','JNB', [(7,0,  8,50), (10,0,  11,50), (14,0,  15,50), (18,0,  19,50), (21,0,  22,50)], 80, 180, None, 'B1'),
        # NBO ↔ EBB — regional
        ('NBO','EBB', [(7,0,  8,10), (14,0,  15,10), (19,0,  20,10)],                    70,  160,  None, 'A4'),
        ('EBB','NBO', [(8,0,  9,10), (15,0,  16,10), (20,0,  21,10)],                    70,  160,  None, 'G2'),
        # NBO ↔ MBA — domestic
        ('NBO','MBA', [(6,0,  7,0 ), (12,0,  13,0 ), (18,0,  19,0 )],                    60,  140,  None, 'A5'),
        ('MBA','NBO', [(7,30, 8,30), (13,30, 14,30), (19,30, 20,30)],                    60,  140,  None, 'H1'),
        # NBO ↔ KGL
        ('NBO','KGL', [(8,0,  9,40), (15,0,  16,40)],                                   100,  230,  None, 'A6'),
        ('KGL','NBO', [(7,0,  8,40), (14,0,  15,40)],                                   100,  230,  None, 'J1'),
    ]

    fn_counter = {'SW': 100}
    flights_added = 0
    ac_idx = 0

    for orig, dest, times, eco, biz, first, gate in schedules:
        if orig not in ap or dest not in ap:
            continue
        key = (ap[orig], ap[dest])
        if key not in routes:
            continue
        route = routes[key]

        # Pick aircraft — bigger for international routes
        if first:
            ac = next((a for a in aircraft if a.first_class_seats > 0), aircraft[0])
        elif eco > 140:
            ac = next((a for a in aircraft if a.economy_seats >= 140 and a.first_class_seats == 0), aircraft[0])
        else:
            ac = aircraft[ac_idx % len(aircraft)]

        # Generate flights for next 14 days
        for day_offset in range(0, 14):
            flight_date = today + timedelta(days=day_offset)
            for dep_h, dep_m, arr_h, arr_m in times:
                dep = flight_date.replace(hour=dep_h, minute=dep_m)
                arr = flight_date.replace(hour=arr_h, minute=arr_m)
                if arr <= dep:
                    arr += timedelta(days=1)

                fn_counter['SW'] += 1
                f = Flight(
                    flight_number=f"SW{fn_counter['SW']}",
                    route_id=route.id,
                    aircraft_id=ac.id,
                    departure_datetime=dep,
                    arrival_datetime=arr,
                    departure_gate=gate,
                    arrival_gate=None,
                    status='scheduled',
                    economy_price=eco,
                    business_price=biz,
                    first_class_price=first,
                    created_by=admin.id if admin else None,
                )
                db.session.add(f)
                flights_added += 1

        ac_idx += 1

    db.session.commit()
    print(f"  [ok] seeded {flights_added} flights (14-day schedule)")


def seed_bookings():
    from app.models.booking import Booking
    from app.models.ticket import Ticket
    from app.models.payment import Payment
    from app.models.passenger import Passenger
    from app.models.flight import Flight
    from app.models.seat import Seat
    from app.models.user import User

    if Booking.query.count() > 0:
        print("  [skip] bookings already seeded")
        return

    passengers = Passenger.query.all()
    if not passengers:
        print("  [skip] no passengers to seed bookings for")
        return

    flights = Flight.query.filter(
        Flight.departure_datetime >= datetime.utcnow(),
        Flight.status == 'scheduled'
    ).limit(30).all()

    if not flights:
        print("  [skip] no flights available for booking")
        return

    bookings_added = 0
    used_seats = set()  # (flight_id, seat_id)

    booking_scenarios = [
        # (passenger_idx, flight_idx, cabin, status, payment_method)
        (0, 0,  'economy',  'confirmed', 'mobile_money'),
        (0, 2,  'business', 'confirmed', 'card'),
        (0, 5,  'economy',  'pending',   'mobile_money'),
        (1, 1,  'economy',  'confirmed', 'mobile_money'),
        (1, 3,  'business', 'confirmed', 'card'),
        (1, 6,  'economy',  'cancelled', 'mobile_money'),
        (2, 4,  'economy',  'confirmed', 'card'),
        (2, 7,  'economy',  'checked_in','card'),
        (2, 8,  'business', 'pending',   'mobile_money'),
    ]

    for p_idx, f_idx, cabin, status, pay_method in booking_scenarios:
        if p_idx >= len(passengers) or f_idx >= len(flights):
            continue

        passenger = passengers[p_idx]
        flight    = flights[f_idx]

        # Find an available seat of the right class
        excluded = [s for (fi, s) in used_seats if fi == flight.id]
        seat_q = Seat.query.filter(
            Seat.aircraft_id == flight.aircraft_id,
            Seat.seat_class == cabin,
        )
        if excluded:
            seat_q = seat_q.filter(~Seat.id.in_(excluded))
        seat = seat_q.first()

        if not seat:
            continue

        # Price
        price = float(flight.price_for_class(cabin) or flight.economy_price)

        booking = Booking(
            passenger_id=passenger.id,
            flight_id=flight.id,
            seat_id=seat.id,
            pnr_code=_pnr(),
            cabin_class=cabin,
            fare_amount=price,
            status=status,
            booked_at=datetime.utcnow() - timedelta(days=random.randint(1, 30))
        )
        if status == 'checked_in':
            booking.checked_in_at = datetime.utcnow() - timedelta(hours=2)
        if status == 'cancelled':
            booking.cancelled_at  = datetime.utcnow() - timedelta(days=1)
            booking.cancellation_reason = 'Change of plans'

        db.session.add(booking)
        db.session.flush()
        used_seats.add((flight.id, seat.id))

        # Ticket for non-cancelled, non-pending bookings
        if status in ('confirmed', 'checked_in', 'boarded'):
            ticket = Ticket(
                booking_id=booking.id,
                ticket_number=_ticket_number(),
                barcode=_barcode(),
                status='active'
            )
            db.session.add(ticket)

            # Payment
            payment = Payment(
                booking_id=booking.id,
                amount=price,
                currency='USD',
                payment_method=pay_method,
                provider='MTN Mobile Money' if pay_method == 'mobile_money' else 'Stripe',
                transaction_id='TXN' + ''.join(random.choices(string.digits, k=12)),
                phone_number='+254700000010' if pay_method == 'mobile_money' else None,
                status='completed',
                paid_at=booking.booked_at + timedelta(minutes=5)
            )
            db.session.add(payment)

            # Award loyalty points
            passenger.frequent_flyer_points += int(price * 0.1)

        bookings_added += 1

    db.session.commit()
    print(f"  [ok] seeded {bookings_added} bookings with tickets and payments")


def seed_crew_assignments():
    from app.models.crew import CrewMember, FlightCrewAssignment
    from app.models.flight import Flight
    from app.models.user import User

    if FlightCrewAssignment.query.count() > 0:
        print("  [skip] crew assignments already seeded")
        return

    crew    = CrewMember.query.all()
    flights = Flight.query.filter(
        Flight.departure_datetime >= datetime.utcnow()
    ).limit(10).all()

    admin = User.query.filter_by(role='admin').first()
    if not crew or not flights:
        print("  [skip] no crew/flights for assignments")
        return

    role_map = {
        'pilot':            'captain',
        'co_pilot':         'first_officer',
        'purser':           'purser',
        'flight_attendant': 'cabin_crew',
    }

    assignments_added = 0
    for flight in flights[:5]:
        assigned = set()
        for c in crew:
            if c.id in assigned:
                continue
            assignment = FlightCrewAssignment(
                flight_id=flight.id,
                crew_member_id=c.id,
                role_on_flight=role_map[c.crew_role],
                assigned_by=admin.id if admin else None
            )
            db.session.add(assignment)
            assigned.add(c.id)
            assignments_added += 1

    db.session.commit()
    print(f"  [ok] seeded {assignments_added} crew assignments")


def main():
    print("\n=== SkyWay FMS — Database Seeder ===")
    with app.app_context():
        try:
            seed_users()
            seed_airports()
            seed_aircraft()
            seed_routes()
            seed_flights()
            seed_bookings()
            seed_crew_assignments()
            print("=== Seeding complete ===\n")
        except Exception as e:
            db.session.rollback()
            print(f"[ERROR] Seeding failed: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


if __name__ == '__main__':
    main()
