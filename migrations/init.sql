-- Flight Management System — Initial Database Schema
-- This file is executed once on first container startup via docker-entrypoint-initdb.d

CREATE DATABASE IF NOT EXISTS fms_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE fms_db;

-- Users
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    role ENUM('admin','passenger','crew','manager') NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    last_login DATETIME,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    reset_token VARCHAR(100) NULL,
    reset_token_expires DATETIME NULL,
    INDEX idx_users_email (email),
    INDEX idx_users_reset_token (reset_token)
) ENGINE=InnoDB;

-- Passengers
CREATE TABLE IF NOT EXISTS passengers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL UNIQUE,
    passport_number VARCHAR(255),
    nationality VARCHAR(100),
    date_of_birth DATE,
    gender ENUM('male','female','other'),
    travel_document_expiry DATE,
    frequent_flyer_number VARCHAR(20) UNIQUE,
    frequent_flyer_points INT NOT NULL DEFAULT 0,
    address VARCHAR(255),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Airports
CREATE TABLE IF NOT EXISTS airports (
    id INT AUTO_INCREMENT PRIMARY KEY,
    iata_code CHAR(3) NOT NULL UNIQUE,
    icao_code CHAR(4) UNIQUE,
    name VARCHAR(200) NOT NULL,
    city VARCHAR(100) NOT NULL,
    country VARCHAR(100) NOT NULL,
    timezone VARCHAR(50) NOT NULL,
    latitude DECIMAL(9,6),
    longitude DECIMAL(9,6),
    INDEX idx_airports_iata (iata_code)
) ENGINE=InnoDB;

-- Aircraft
CREATE TABLE IF NOT EXISTS aircraft (
    id INT AUTO_INCREMENT PRIMARY KEY,
    registration_number VARCHAR(20) NOT NULL UNIQUE,
    model VARCHAR(100) NOT NULL,
    manufacturer VARCHAR(100),
    economy_seats INT NOT NULL DEFAULT 0,
    business_seats INT NOT NULL DEFAULT 0,
    first_class_seats INT NOT NULL DEFAULT 0,
    status ENUM('active','maintenance','retired') NOT NULL DEFAULT 'active',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- Seats
CREATE TABLE IF NOT EXISTS seats (
    id INT AUTO_INCREMENT PRIMARY KEY,
    aircraft_id INT NOT NULL,
    seat_number VARCHAR(5) NOT NULL,
    seat_class ENUM('economy','business','first') NOT NULL,
    is_window BOOLEAN NOT NULL DEFAULT FALSE,
    is_aisle BOOLEAN NOT NULL DEFAULT FALSE,
    is_extra_legroom BOOLEAN NOT NULL DEFAULT FALSE,
    UNIQUE KEY uq_seat_aircraft (aircraft_id, seat_number),
    FOREIGN KEY (aircraft_id) REFERENCES aircraft(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Routes
CREATE TABLE IF NOT EXISTS routes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    origin_airport_id INT NOT NULL,
    destination_airport_id INT NOT NULL,
    distance_km INT,
    estimated_duration_minutes INT,
    UNIQUE KEY uq_route (origin_airport_id, destination_airport_id),
    FOREIGN KEY (origin_airport_id) REFERENCES airports(id),
    FOREIGN KEY (destination_airport_id) REFERENCES airports(id)
) ENGINE=InnoDB;

-- Flights
CREATE TABLE IF NOT EXISTS flights (
    id INT AUTO_INCREMENT PRIMARY KEY,
    flight_number VARCHAR(10) NOT NULL,
    route_id INT NOT NULL,
    aircraft_id INT NOT NULL,
    departure_datetime DATETIME NOT NULL,
    arrival_datetime DATETIME NOT NULL,
    departure_gate VARCHAR(10),
    arrival_gate VARCHAR(10),
    status ENUM('scheduled','boarding','departed','arrived','delayed','cancelled') NOT NULL DEFAULT 'scheduled',
    economy_price DECIMAL(10,2) NOT NULL,
    business_price DECIMAL(10,2),
    first_class_price DECIMAL(10,2),
    delay_minutes INT NOT NULL DEFAULT 0,
    delay_reason TEXT,
    cancellation_reason TEXT,
    created_by INT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_flights_departure (departure_datetime),
    INDEX idx_flights_status (status),
    INDEX idx_flights_number (flight_number),
    FOREIGN KEY (route_id) REFERENCES routes(id),
    FOREIGN KEY (aircraft_id) REFERENCES aircraft(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
) ENGINE=InnoDB;

-- Flight archive (soft-delete sink — no FK constraints so records survive referential changes)
CREATE TABLE IF NOT EXISTS flights_archive (
    id INT NOT NULL,
    flight_number VARCHAR(10) NOT NULL,
    route_id INT,
    aircraft_id INT,
    departure_datetime DATETIME NOT NULL,
    arrival_datetime DATETIME NOT NULL,
    departure_gate VARCHAR(10),
    arrival_gate VARCHAR(10),
    status ENUM('scheduled','boarding','departed','arrived','delayed','cancelled') NOT NULL,
    economy_price DECIMAL(10,2) NOT NULL,
    business_price DECIMAL(10,2),
    first_class_price DECIMAL(10,2),
    delay_minutes INT NOT NULL DEFAULT 0,
    delay_reason TEXT,
    cancellation_reason TEXT,
    created_by INT,
    created_at DATETIME,
    updated_at DATETIME,
    archived_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    archived_by INT,
    PRIMARY KEY (id)
) ENGINE=InnoDB;

-- Bookings
CREATE TABLE IF NOT EXISTS bookings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    passenger_id INT NOT NULL,
    flight_id INT NOT NULL,
    seat_id INT NOT NULL,
    pnr_code VARCHAR(6) NOT NULL UNIQUE,
    cabin_class ENUM('economy','business','first') NOT NULL,
    fare_amount DECIMAL(10,2) NOT NULL,
    status ENUM('pending','confirmed','cancelled','checked_in','boarded','no_show') NOT NULL DEFAULT 'pending',
    special_requests TEXT,
    booked_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    checked_in_at DATETIME,
    cancelled_at DATETIME,
    cancellation_reason TEXT,
    UNIQUE KEY uq_booking_seat (flight_id, seat_id),
    INDEX idx_bookings_pnr (pnr_code),
    INDEX idx_bookings_passenger (passenger_id),
    INDEX idx_bookings_flight (flight_id),
    FOREIGN KEY (passenger_id) REFERENCES passengers(id),
    FOREIGN KEY (flight_id) REFERENCES flights(id),
    FOREIGN KEY (seat_id) REFERENCES seats(id)
) ENGINE=InnoDB;

-- Tickets
CREATE TABLE IF NOT EXISTS tickets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    booking_id INT NOT NULL UNIQUE,
    ticket_number VARCHAR(20) NOT NULL UNIQUE,
    barcode VARCHAR(100) NOT NULL UNIQUE,
    status ENUM('active','used','cancelled') NOT NULL DEFAULT 'active',
    issued_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (booking_id) REFERENCES bookings(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Payments
CREATE TABLE IF NOT EXISTS payments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    booking_id INT NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    currency CHAR(3) NOT NULL DEFAULT 'USD',
    payment_method ENUM('mobile_money','card','bank_transfer') NOT NULL,
    provider VARCHAR(50),
    transaction_id VARCHAR(100) UNIQUE,
    phone_number VARCHAR(20),
    status ENUM('pending','completed','failed','refunded') NOT NULL DEFAULT 'pending',
    paid_at DATETIME,
    refunded_at DATETIME,
    refund_amount DECIMAL(10,2),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_payments_booking (booking_id),
    FOREIGN KEY (booking_id) REFERENCES bookings(id)
) ENGINE=InnoDB;

-- Crew members
CREATE TABLE IF NOT EXISTS crew_members (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL UNIQUE,
    employee_id VARCHAR(20) NOT NULL UNIQUE,
    crew_role ENUM('pilot','co_pilot','flight_attendant','purser') NOT NULL,
    license_number VARCHAR(50),
    certification_expiry DATE,
    medical_expiry DATE,
    hire_date DATE,
    status ENUM('active','on_leave','retired') NOT NULL DEFAULT 'active',
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Flight crew assignments
CREATE TABLE IF NOT EXISTS flight_crew_assignments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    flight_id INT NOT NULL,
    crew_member_id INT NOT NULL,
    role_on_flight ENUM('captain','first_officer','purser','cabin_crew') NOT NULL,
    assigned_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    assigned_by INT,
    UNIQUE KEY uq_flight_crew (flight_id, crew_member_id),
    FOREIGN KEY (flight_id) REFERENCES flights(id) ON DELETE CASCADE,
    FOREIGN KEY (crew_member_id) REFERENCES crew_members(id),
    FOREIGN KEY (assigned_by) REFERENCES users(id)
) ENGINE=InnoDB;

-- Notifications
CREATE TABLE IF NOT EXISTS notifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    type ENUM('booking_confirmed','flight_delayed','flight_cancelled','boarding_reminder','payment_received','check_in_open') NOT NULL,
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    email_sent BOOLEAN NOT NULL DEFAULT FALSE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_notifications_user (user_id, is_read),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Audit logs
CREATE TABLE IF NOT EXISTS audit_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    action ENUM('CREATE','UPDATE','DELETE','LOGIN','LOGOUT','PAYMENT') NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id INT,
    description TEXT,
    ip_address VARCHAR(45),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_audit_logs_user (user_id),
    INDEX idx_audit_logs_entity (entity_type, entity_id),
    INDEX idx_audit_logs_created (created_at),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- Seed: default admin user (password: Admin@1234)
-- Password hash for 'Admin@1234' using bcrypt cost 12
INSERT IGNORE INTO users (email, password_hash, first_name, last_name, role)
VALUES (
    'admin@airline.com',
    '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36Wr0NrLHifdIWjFsWlNPO2',
    'System',
    'Admin',
    'admin'
);
