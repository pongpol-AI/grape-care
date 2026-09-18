"""Kaolad Farm API. Hardware adapters are intentionally not implemented in V1."""
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship, sessionmaker

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"; DATA.mkdir(exist_ok=True)
STATIC = ROOT / "app" / "static"; STATIC.mkdir(exist_ok=True)
engine = create_engine(f"sqlite:///{DATA / 'kaolad_farm.db'}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)

class Base(DeclarativeBase): pass
class Plant(Base):
    __tablename__ = "plants"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    plant_id: Mapped[str] = mapped_column(String(40), unique=True)
    nickname: Mapped[str] = mapped_column(String(100))
    variety: Mapped[str] = mapped_column(String(100))
    planted_on: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    stage: Mapped[str] = mapped_column(String(100), default="ฟื้นฟูต้น")
    health: Mapped[str] = mapped_column(String(30), default="ปกติ")
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
class Task(Base):
    __tablename__ = "tasks"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    plant_id: Mapped[Optional[int]] = mapped_column(ForeignKey("plants.id"), nullable=True)
    task_type: Mapped[str] = mapped_column(String(80))
    description: Mapped[str] = mapped_column(Text, default="")
    due_date: Mapped[date] = mapped_column(Date)
    priority: Mapped[str] = mapped_column(String(20), default="normal")
    status: Mapped[str] = mapped_column(String(20), default="open")
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    plant: Mapped[Optional[Plant]] = relationship()
class CareHistory(Base):
    __tablename__ = "care_history"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    plant_id: Mapped[Optional[int]] = mapped_column(ForeignKey("plants.id"), nullable=True)
    event_type: Mapped[str] = mapped_column(String(80))
    note: Mapped[str] = mapped_column(Text, default="")
    happened_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
class SensorDevice(Base):
    __tablename__ = "sensor_devices"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sensor_type: Mapped[str] = mapped_column(String(80), unique=True)
    status: Mapped[str] = mapped_column(String(20), default="NOT_INSTALLED")
class Alert(Base):
    __tablename__ = "alerts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    level: Mapped[str] = mapped_column(String(20))
    message: Mapped[str] = mapped_column(Text)
    is_open: Mapped[int] = mapped_column(Integer, default=1)

class PlantIn(BaseModel):
    plant_id: str; nickname: str; variety: str; planted_on: Optional[date] = None
    location: Optional[str] = None; stage: str = "ฟื้นฟูต้น"; health: str = "ปกติ"; note: Optional[str] = None
class TaskIn(BaseModel):
    plant_id: Optional[int] = None; task_type: str; description: str = ""; due_date: date; priority: str = "normal"

app = FastAPI(title="Kaolad Farm – Smart Grape Garden")
app.mount("/static", StaticFiles(directory=STATIC), name="static")
def db(): return SessionLocal()
def plant_out(p): return {"id":p.id,"plant_id":p.plant_id,"nickname":p.nickname,"variety":p.variety,"stage":p.stage,"health":p.health,"location":p.location,"note":p.note,"planted_on":str(p.planted_on) if p.planted_on else None}
def task_out(t): return {"id":t.id,"plant":t.plant.nickname if t.plant else "ทั้งสวน","task_type":t.task_type,"description":t.description,"due_date":str(t.due_date),"priority":t.priority,"status":t.status}

@app.on_event("startup")
def setup():
    Base.metadata.create_all(engine)
    with db() as s:
        for name in ["temperature","air_humidity","soil_moisture","light","rainfall","water_tank","leaf_wetness"]:
            if not s.query(SensorDevice).filter_by(sensor_type=name).first(): s.add(SensorDevice(sensor_type=name))
        s.commit()

@app.get("/api/dashboard")
def dashboard():
    with db() as s:
        plants=s.query(Plant).all(); tasks=s.query(Task).filter(Task.status=="open").order_by(Task.due_date).all()
        sensors=s.query(SensorDevice).all()
        return {"garden_status":"ยังไม่มีข้อมูลเพียงพอ" if not plants else "ปกติ","irrigation":"NOT_INSTALLED","disease_risk":"UNKNOWN","plants":[plant_out(p) for p in plants],"tasks":[task_out(t) for t in tasks],"sensors":[{"type":x.sensor_type,"status":x.status,"value":None} for x in sensors],"alerts":[{"level":a.level,"message":a.message} for a in s.query(Alert).filter_by(is_open=1).all()]}
@app.get("/api/plants")
def plants():
    with db() as s: return [plant_out(p) for p in s.query(Plant).all()]
@app.post("/api/plants", status_code=201)
def add_plant(data: PlantIn):
    with db() as s:
        if s.query(Plant).filter_by(plant_id=data.plant_id).first(): raise HTTPException(409,"Plant ID นี้มีอยู่แล้ว")
        p=Plant(**data.model_dump());s.add(p);s.commit();s.refresh(p);return plant_out(p)
@app.put("/api/plants/{plant_id}")
def edit_plant(plant_id:int,data:PlantIn):
    with db() as s:
        p=s.get(Plant,plant_id)
        if not p: raise HTTPException(404,"ไม่พบต้นองุ่น")
        for k,v in data.model_dump().items(): setattr(p,k,v)
        s.commit();return plant_out(p)
@app.delete("/api/plants/{plant_id}",status_code=204)
def delete_plant(plant_id:int):
    with db() as s:
        p=s.get(Plant,plant_id)
        if not p: raise HTTPException(404,"ไม่พบต้นองุ่น")
        s.delete(p);s.commit()
@app.post("/api/tasks",status_code=201)
def add_task(data:TaskIn):
    with db() as s:
        if data.plant_id and not s.get(Plant,data.plant_id): raise HTTPException(404,"ไม่พบต้นองุ่น")
        t=Task(**data.model_dump());s.add(t);s.commit();s.refresh(t);return task_out(t)
@app.post("/api/tasks/{task_id}/complete")
def complete_task(task_id:int):
    with db() as s:
        t=s.get(Task,task_id)
        if not t: raise HTTPException(404,"ไม่พบงาน")
        t.status="completed";t.completed_at=datetime.now();s.add(CareHistory(plant_id=t.plant_id,event_type=t.task_type,note=t.description));s.commit();return {"ok":True,"message":"บันทึกงานและประวัติแล้ว"}
@app.get("/api/sensors")
def sensors():
    with db() as s:return [{"type":x.sensor_type,"status":x.status,"value":None,"message":"ยังไม่ได้ติดตั้ง Sensor" if x.status=="NOT_INSTALLED" else "ไม่มีข้อมูล"} for x in s.query(SensorDevice).all()]
@app.post("/api/sensors/readings",status_code=501)
def future_sensor_endpoint(): raise HTTPException(501,"ยังไม่ได้เชื่อมต่ออุปกรณ์ ESP32")
@app.get("/")
def home(): return FileResponse(STATIC / "index.html")
