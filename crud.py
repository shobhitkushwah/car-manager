from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.models import Car
from backend.schemas import CarCreate, CarUpdate, CarResponse

def get_cars(db: Session, skip: int = 0, limit: int = 100):
    """GET /cars - All cars"""
    return db.query(Car).offset(skip).limit(limit).all()

def get_car_by_id(db: Session, car_id: str):
    """GET /car/{car_id} - Single car"""
    return db.query(Car).filter(Car.car_id == car_id).first()

def create_car(db: Session, car: CarCreate) -> Car:
    """POST /car - Create new car"""
    db_car = Car(**car.model_dump())
    db.add(db_car)
    db.commit()
    db.refresh(db_car)
    return db_car

def update_car_full(db: Session, car_id: str, car: CarCreate) -> Car:
    """PUT /car/{car_id} - Full update"""
    db_car = get_car_by_id(db, car_id)
    if not db_car:
        raise ValueError("Car not found")
    
    # Full replace
    for field, value in car.model_dump().items():
        setattr(db_car, field, value)
    db.commit()
    db.refresh(db_car)
    return db_car

def update_car_partial(db: Session, car_id: str, car_update: CarUpdate) -> Car:
    """PATCH /car/{car_id} - Partial update"""
    db_car = get_car_by_id(db, car_id)
    if not db_car:
        raise ValueError("Car not found")
    
    update_data = car_update.model_dump(exclude_unset=True)
    if not update_data:
        raise ValueError("No fields to update")
    
    for field, value in update_data.items():
        setattr(db_car, field, value)
    db.commit()
    db.refresh(db_car)
    return db_car

def delete_car(db: Session, car_id: str) -> bool:
    """DELETE /car/{car_id}"""
    db_car = get_car_by_id(db, car_id)
    if not db_car:
        return False
    
    db.delete(db_car)
    db.comm
