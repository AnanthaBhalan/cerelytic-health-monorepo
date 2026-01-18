from sqlalchemy import Column, Integer, String, DateTime, Float, Text, JSON, ForeignKey, Enum, Index
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from database import Base


class UserRole(enum.Enum):
    USER = "user"
    ADMIN = "admin"


class BillStatus(enum.Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)  # matches X-User-Id
    email = Column(String, unique=True, index=True, nullable=True)
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    bills = relationship("Bill", back_populates="user")


class Bill(Base):
    __tablename__ = "bills"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)

    status = Column(Enum(BillStatus), default=BillStatus.QUEUED, nullable=False, index=True)
    file_url = Column(String, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="bills")
    analysis = relationship(
        "Analysis",
        back_populates="bill",
        uselist=False,
        cascade="all, delete-orphan"
    )


class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)
    bill_id = Column(Integer, ForeignKey("bills.id"), nullable=False, unique=True, index=True)

    fraud_score = Column(Float, nullable=True)
    summary = Column(Text, nullable=True)
    details = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    bill = relationship("Bill", back_populates="analysis")
