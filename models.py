from sqlalchemy import Column, String, Integer
from backend.database import Base

class Car(Base):
    __tablename__ = "cars"
    
    car_id = Column(String(20), primary_key=True, index=True)
    brand = Column(String(50), nullable=False)
    model = Column(String(50), nullable=False)
    year = Column(Integer, nullable=False)
    price = Column(Integer, nullable=False)
