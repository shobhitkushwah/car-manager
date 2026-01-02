from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, String, Integer, func
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from typing import List
from pydantic import BaseModel
import json

# ================= DATABASE =================
engine = create_engine(
    "sqlite:///./cars.db",
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ================= SCHEMAS =================
class CarBase(BaseModel):
    car_id: str
    brand: str
    model: str
    year: int
    price: int

class CarCreate(CarBase):
    pass

class CarUpdate(BaseModel):
    brand: str
    model: str
    year: int
    price: int

class CarResponse(CarBase):
    class Config:
        from_attributes = True

# ================= MODEL =================
class Car(Base):
    __tablename__ = "cars"

    car_id = Column(String(10), primary_key=True, index=True)
    brand = Column(String(50))
    model = Column(String(100))
    year = Column(Integer)
    price = Column(Integer)

Base.metadata.create_all(bind=engine)

# ================= DB DEP =================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ================= CRUD =================
def get_all_cars(db: Session):
    return db.query(Car).all()

def get_car_by_id(db: Session, car_id: str):
    return db.query(Car).filter(Car.car_id == car_id).first()

def create_car(db: Session, car: CarCreate):
    if get_car_by_id(db, car.car_id):
        raise HTTPException(status_code=400, detail="Car already exists")

    db_car = Car(**car.dict())
    db.add(db_car)
    db.commit()
    db.refresh(db_car)
    return db_car

def update_car(db: Session, car_id: str, car: CarUpdate):
    db_car = get_car_by_id(db, car_id)
    if not db_car:
        raise HTTPException(status_code=404, detail="Car not found")

    for key, value in car.dict().items():
        setattr(db_car, key, value)

    db.commit()
    db.refresh(db_car)
    return db_car

def delete_car(db: Session, car_id: str):
    db_car = get_car_by_id(db, car_id)
    if not db_car:
        raise HTTPException(status_code=404, detail="Car not found")

    db.delete(db_car)
    db.commit()
    return {"message": "Car deleted successfully"}

# ================= APP =================
app = FastAPI(title="🚗 Car Manager API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================= ROUTES =================
@app.get("/")
def root():
    return {"message": "🚗 Car API is running"}

# Get all cars
@app.get("/cars", response_model=List[CarResponse])
def read_cars(db: Session = Depends(get_db)):
    return get_all_cars(db)

# Get single car
@app.get("/cars/{car_id}", response_model=CarResponse)
def read_car(car_id: str, db: Session = Depends(get_db)):
    car = get_car_by_id(db, car_id)
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")
    return car

# Add car
@app.post("/cars", response_model=CarResponse)
def add_car(car: CarCreate, db: Session = Depends(get_db)):
    return create_car(db, car)

# Update car
@app.put("/cars/{car_id}", response_model=CarResponse)
def edit_car(car_id: str, car: CarUpdate, db: Session = Depends(get_db)):
    return update_car(db, car_id, car)

# Delete car
@app.delete("/cars/{car_id}")
def remove_car(car_id: str, db: Session = Depends(get_db)):
    return delete_car(db, car_id)

# Stats
@app.get("/stats")
def stats(db: Session = Depends(get_db)):
    return {
        "total_cars": db.query(Car).count(),
        "average_price": round(db.query(func.avg(Car.price)).scalar() or 0)
    }

# JSON Migration
@app.post("/migrate")
def migrate(db: Session = Depends(get_db)):
    try:
        with open("../data/car.json") as f:
            data = json.load(f)

        for item in data.values():
            if not get_car_by_id(db, item["car_id"]):
                create_car(db, CarCreate(**item))

        return {"message": "✅ Data migrated successfully"}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="car.json not found")
