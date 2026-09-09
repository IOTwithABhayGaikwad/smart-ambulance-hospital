import os, random, asyncio
from datetime import datetime, timezone
from typing import Optional
from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from passlib.context import CryptContext
from jose import jwt

app = FastAPI(title="Smart Ambulance Hospital Pre-Alert API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET = os.getenv("JWT_SECRET", "change-this-demo-secret")
patients = {
    "P001": {"id":"P001","name":"Demo Patient","age":52,"gender":"Male","emergency_type":"Respiratory distress","ambulance_id":"AMB-01"},
    "P002": {"id":"P002","name":"Demo Patient 2","age":34,"gender":"Female","emergency_type":"Trauma","ambulance_id":"AMB-02"},
}
ambulances = {
    "AMB-01":{"id":"AMB-01","registration":"MH-00-AA-0001","driver":"Demo Driver","status":"En Route","patient_id":"P001","destination":"City General Hospital","lat":19.9975,"lng":73.7898,"speed":48,"eta":12},
    "AMB-02":{"id":"AMB-02","registration":"MH-00-BB-0002","driver":"Demo Driver 2","status":"Available","patient_id":"P002","destination":"City General Hospital","lat":20.001,"lng":73.781,"speed":0,"eta":0}
}
vitals = {
    "P001":{"patient_id":"P001","ambulance_id":"AMB-01","heart_rate":112,"spo2":93,"temperature":38.1,"respiratory_rate":24,"ecg":72,"lat":19.9975,"lng":73.7898,"timestamp":datetime.now(timezone.utc).isoformat()},
    "P002":{"patient_id":"P002","ambulance_id":"AMB-02","heart_rate":78,"spo2":98,"temperature":36.8,"respiratory_rate":16,"ecg":70,"lat":20.001,"lng":73.781,"timestamp":datetime.now(timezone.utc).isoformat()}
}
alerts=[]
history=[]

def risk(hr, spo2, temp, rr):
    s=0; reasons=[]
    if spo2 < 90: s+=40; reasons.append("Low SpO₂")
    elif spo2 < 94: s+=25; reasons.append("Reduced SpO₂")
    if hr > 120 or hr < 50: s+=25; reasons.append("Abnormal heart rate")
    elif hr > 100: s+=10; reasons.append("Elevated heart rate")
    if temp >= 39 or temp < 35: s+=20; reasons.append("Abnormal temperature")
    elif temp >= 38: s+=10; reasons.append("Elevated temperature")
    if rr > 30 or rr < 10: s+=20; reasons.append("Abnormal respiratory rate")
    elif rr > 20: s+=10; reasons.append("Increased respiratory rate")
    s=min(100,s)
    level="CRITICAL" if s>=75 else "HIGH" if s>=50 else "MEDIUM" if s>=25 else "LOW"
    return s,level,reasons

class VitalsIn(BaseModel):
    patient_id: str
    ambulance_id: str
    heart_rate: int = Field(ge=20, le=250)
    spo2: int = Field(ge=50, le=100)
    temperature: float = Field(ge=25, le=45)
    respiratory_rate: int = Field(ge=4, le=80)
    ecg: Optional[float]=None
    latitude: float = -0.0
    longitude: float = -0.0
    timestamp: Optional[str]=None

class Login(BaseModel):
    email: str
    password: str

class AlertIn(BaseModel):
    patient_id: str
    ambulance_id: str
    message: str

@app.get("/api/health")
def health(): return {"ok":True,"service":"smart-ambulance-api"}

@app.post("/api/login")
def login(x: Login):
    # Demo authentication: demo@hospital.com / demo123
    if x.email=="demo@hospital.com" and x.password=="demo123":
        return {"access_token":jwt.encode({"sub":x.email},"JWT_SECRET",algorithm="HS256"),"user":{"email":x.email,"role":"doctor"}}
    raise HTTPException(401,"Invalid demo credentials")

@app.get("/api/patients")
def get_patients(): return list(patients.values())

@app.get("/api/patients/{patient_id}")
def get_patient(patient_id:str):
    if patient_id not in patients: raise HTTPException(404,"Patient not found")
    p=patients[patient_id].copy(); p["vitals"]=vitals.get(patient_id); p["risk"]=get_risk(patient_id); return p

@app.get("/api/ambulances")
def get_ambulances(): return list(ambulances.values())

@app.get("/api/ambulances/{ambulance_id}")
def get_ambulance(ambulance_id:str):
    if ambulance_id not in ambulances: raise HTTPException(404,"Ambulance not found")
    return ambulances[ambulance_id]

@app.get("/api/vitals")
def get_vitals(): return list(vitals.values())

@app.post("/api/vitals")
async def post_vitals(x:VitalsIn):
    if x.patient_id not in patients: raise HTTPException(404,"Patient not found")
    score,level,reasons=risk(x.heart_rate,x.spo2,x.temperature,x.respiratory_rate)
    d=x.model_dump()
    d["timestamp"]=x.timestamp or datetime.now(timezone.utc).isoformat()
    vitals[x.patient_id]=d
    history.append({**d,"risk_score":score,"risk_level":level})
    if x.ambulance_id in ambulances:
        ambulances[x.ambulance_id].update({"lat":x.latitude,"lng":x.longitude,"status":"Emergency" if level=="CRITICAL" else "En Route"})
    if level=="CRITICAL":
        alerts.insert(0,{"id":len(alerts)+1,"patient_id":x.patient_id,"ambulance_id":x.ambulance_id,"level":level,"message":"Critical vital signs detected","reasons":reasons,"timestamp":d["timestamp"],"acknowledged":False})
    await broadcast({"type":"vitals","data":d,"risk":{"score":score,"level":level,"reasons":reasons}})
    return {**d,"risk_score":score,"risk_level":level,"reasons":reasons}

@app.post("/api/demo/{scenario}")
async def demo(scenario:str):
    scenarios={
      "normal":(78,98,36.8,16),
      "medium":(106,94,37.8,21),
      "high":(125,91,38.4,27),
      "critical":(145,84,39.2,34)
    }
    if scenario not in scenarios: raise HTTPException(400,"Scenario must be normal, medium, high or critical")
    hr,sp,t,rr=scenarios[scenario]
    return await post_vitals(VitalsIn(patient_id="P001",ambulance_id="AMB-01",heart_rate=hr,spo2=sp,temperature=t,respiratory_rate=rr,ecg=72,latitude=19.9975,longitude=73.7898))

def get_risk(pid):
    v=vitals.get(pid)
    if not v: return {"score":0,"level":"UNKNOWN","reasons":[]}
    s,l,r=risk(v["heart_rate"],v["spo2"],v["temperature"],v["respiratory_rate"])
    return {"score":s,"level":l,"reasons":r}

@app.get("/api/risk/{patient_id}")
def risk_endpoint(patient_id:str):
    if patient_id not in patients: raise HTTPException(404,"Patient not found")
    return get_risk(patient_id)

@app.get("/api/alerts")
def get_alerts(): return alerts[:100]

@app.post("/api/alerts")
async def create_alert(x:AlertIn):
    a={"id":len(alerts)+1,**x.model_dump(),"level":"CRITICAL","timestamp":datetime.now(timezone.utc).isoformat(),"acknowledged":False}
    alerts.insert(0,a); await broadcast({"type":"alert","data":a}); return a

@app.get("/api/history/{patient_id}")
def get_history(patient_id:str): return [h for h in history if h["patient_id"]==patient_id][-100:]

@app.get("/api/location/{ambulance_id}")
def location(ambulance_id:str):
    if ambulance_id not in ambulances: raise HTTPException(404,"Ambulance not found")
    a=ambulances[ambulance_id]
    return {"ambulance_id":ambulance_id,"latitude":a["lat"],"longitude":a["lng"],"speed":a["speed"],"eta":a["eta"],"destination":a["destination"]}

class ConnectionManager:
    def __init__(self): self.clients=[]
    async def connect(self,ws): await ws.accept(); self.clients.append(ws)
    def disconnect(self,ws):
        if ws in self.clients:self.clients.remove(ws)
    async def send(self,msg):
        for ws in list(self.clients):
            try: await ws.send_json(msg)
            except: self.disconnect(ws)
manager=ConnectionManager()

async def broadcast(msg): await manager.send(msg)

@app.websocket("/ws")
async def websocket(ws:WebSocket):
    await manager.connect(ws)
    try:
        while True: await ws.receive_text()
    except WebSocketDisconnect: manager.disconnect(ws)