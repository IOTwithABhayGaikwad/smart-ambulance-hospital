
CREATE TABLE users (id SERIAL PRIMARY KEY, email TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, role TEXT NOT NULL, created_at TIMESTAMPTZ DEFAULT now());
CREATE TABLE patients (id TEXT PRIMARY KEY, name TEXT, age INT, gender TEXT, emergency_type TEXT, ambulance_id TEXT);
CREATE TABLE ambulances (id TEXT PRIMARY KEY, registration TEXT, driver TEXT, status TEXT, patient_id TEXT, destination TEXT, latitude DOUBLE PRECISION, longitude DOUBLE PRECISION);
CREATE TABLE vitals (id BIGSERIAL PRIMARY KEY, patient_id TEXT REFERENCES patients(id), ambulance_id TEXT, heart_rate INT, spo2 INT, temperature NUMERIC, respiratory_rate INT, ecg JSONB, latitude DOUBLE PRECISION, longitude DOUBLE PRECISION, risk_score INT, risk_level TEXT, created_at TIMESTAMPTZ DEFAULT now());
CREATE TABLE alerts (id BIGSERIAL PRIMARY KEY, patient_id TEXT REFERENCES patients(id), ambulance_id TEXT, level TEXT, message TEXT, reasons JSONB, acknowledged BOOLEAN DEFAULT FALSE, created_at TIMESTAMPTZ DEFAULT now());
CREATE TABLE locations (id BIGSERIAL PRIMARY KEY, ambulance_id TEXT, latitude DOUBLE PRECISION, longitude DOUBLE PRECISION, speed NUMERIC, eta INT, created_at TIMESTAMPTZ DEFAULT now());
CREATE TABLE emergency_events (id BIGSERIAL PRIMARY KEY, patient_id TEXT, ambulance_id TEXT, event_type TEXT, details JSONB, created_at TIMESTAMPTZ DEFAULT now());
