from sqlalchemy import (
    Column, Integer, String, ForeignKey, Boolean, DECIMAL, TIMESTAMP, func
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.asyncio import AsyncAttrs
from app.db.db import Base


class User(Base, AsyncAttrs):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(100), nullable=False)
    semester = Column(String(50))
    department = Column(String(100))
    year = Column(String(10))
    role = Column(String, nullable=False)
    password = Column(String(255), nullable=False)

    print_requests = relationship("PrintRequest", back_populates="user")


class PrintRequest(Base, AsyncAttrs):
    __tablename__ = "print_request"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    file_path = Column(String(550), nullable=False)
    color = Column(Boolean, nullable=False, default=False)
    sides = Column(String, nullable=False)
    orientation = Column(String, nullable=False)
    pages = Column(String(50), nullable=False)
    status = Column(String, nullable=False, default="waiting")
    payment_status = Column(String, nullable=False, default="pending")
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="print_requests")
    payment = relationship("Payment", back_populates="print_request", uselist=False)


class Payment(Base, AsyncAttrs):
    __tablename__ = "payment"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    print_request_id = Column(Integer, ForeignKey("print_request.id"))
    amount = Column(DECIMAL(10, 2), nullable=False)
    payment_method = Column(String, nullable=False)
    paid_at = Column(TIMESTAMP(timezone=True))

    print_request = relationship("PrintRequest", back_populates="payment")
