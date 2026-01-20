from sqlalchemy import Column, String, Integer, JSON
from database import Base


class Bill(Base):
    __tablename__ = "bills"

    id = Column(String, primary_key=True)
    status = Column(String)
    fraud_score = Column(Integer)
    details = Column(JSON)
