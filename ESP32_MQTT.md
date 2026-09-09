
# ESP32 → MQTT integration

Topic:
`ambulance/{ambulance_id}/patient/{patient_id}/vitals`

Payload:
```json
{
  "patient_id":"P001",
  "ambulance_id":"AMB-01",
  "heart_rate":118,
  "spo2":91,
  "temperature":38.4,
  "respiratory_rate":26,
  "latitude":19.9975,
  "longitude":73.7898
}
```

The backend API accepts the same fields at `POST /api/vitals`. In production, use an MQTT subscriber worker (paho-mqtt or asyncio-mqtt) to validate and forward MQTT messages into the same processing function. Keep broker credentials in `.env`, never in frontend code.
