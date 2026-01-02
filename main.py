from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import json

from backend.database import get_db, engine
from backend.models import Car
from backend.schemas import CarCreate, CarResponse, CarUpdate
from backend.crud import (get_cars, get_car_by_id, create_car, 
                         update_car, delete_car)

# Tables create
Car.metadata.create_all(bind=engine)

app = FastAPI(title="🚗 Car Manager API", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", tags=["Home"])
async def root():
    return {"message": "🚗 Car Manager API v2.0", "docs": "/docs"}

@app.get("/cars", response_model=List[CarResponse], tags=["Cars"])
async def read_cars(skip: int = 0, limit: int = Query(100, le=1000), db: Session = Depends(get_db)):
    cars = get_cars(db, skip=skip, limit=limit)
    return cars

@app.get("/car/{car_id}", response_model=CarResponse, tags=["Cars"])
async def read_car(car_id: str, db: Session = Depends(get_db)):
    car = get_car_by_id(db, car_id)
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")
    return car

@app.post("/car", response_model=CarResponse, tags=["Cars"])
async def create_car_endpoint(car: CarCreate, db: Session = Depends(get_db)):
    return create_car(db, car)

@app.put("/car/{car_id}", response_model=CarResponse, tags=["Cars"])
async def update_car_endpoint(car_id: str, car: CarUpdate, db: Session = Depends(get_db)):
    updated_car = update_car(db, car_id, car)
    if not updated_car:
        raise HTTPException(status_code=404, detail="Car not found")
    return updated_car

@app.delete("/car/{car_id}", tags=["Cars"])
async def delete_car_endpoint(car_id: str, db: Session = Depends(get_db)):
    if not delete_car(db, car_id):
        raise HTTPException(status_code=404, detail="Car not found")
    return {"message": "Car deleted successfully"}

@app.get("/cars/sort", tags=["Cars"])
async def sort_cars(sort_by: str = Query("price", regex="^(price|year)$"), 
                   order: str = Query("asc", regex="^(asc|desc)$"), 
                   db: Session = Depends(get_db)):
    cars = get_cars(db)
    cars.sort(key=lambda x: getattr(x, sort_by), reverse=(order == "desc"))
    return cars

@app.get("/stats", tags=["Stats"])
async def get_stats(db: Session = Depends(get_db)):
    total = db.query(Car).count()
    avg_price = db.query(func.avg(Car.price)).scalar() or 0
    return {
        "total_cars": total,
        "avg_price": round(float(avg_price)),
        "min_price": db.query(func.min(Car.price)).scalar(),
        "max_price": db.query(func.max(Car.price)).scalar()
    }

@app.post("/migrate", tags=["Migration"])
async def migrate_json(db: Session = Depends(get_db)):
    try:
        with open("../data/car.json", "r") as f:
            data = json.load(f)
        
        count = 0
        for car_data in data.values():
            if not get_car_by_id(db, car_data["car_id"]):
                create_car(db, CarCreate(**car_data))
                count += 1
        db.commit()
        return {"message": f"✅ Migrated {count} cars from JSON"}
    except FileNotFoundError:
        raise HTTPException(404, "car.json not found")
