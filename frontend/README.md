
# Smart Ambulance – Hospital Pre-Alert System

Full-stack educational prototype.

## Demo login
Email: `demo@hospital.com`
Password: `demo123`

## Run backend
```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

## Run frontend
```bash
cd frontend
npm install
npm run dev
```

Open the Vite URL shown in the terminal.

## Demo scenarios
Dashboard buttons generate normal/medium/high/critical vitals through the backend. "Simulate Emergency" creates a critical case and an alert.

## Important
This version uses in-memory demo data so it runs immediately. The PostgreSQL schema is included in `database/schema.sql` for the next production-style step. MQTT hardware integration is documented in `docs/ESP32_MQTT.md`.

Use synthetic patient data only. This is not a certified medical device.
