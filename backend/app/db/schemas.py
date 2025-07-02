from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

class UserCreate(BaseModel):
    username: str
    password: str
    semester: str | None = None
    department: str | None = None
    year: str | None = None

class UserResponse(BaseModel):
    id: int
    username: str
    semester: str | None = None
    department: str | None = None
    year: str | None = None

    class Config:
        orm_mode = True

class PaymentResponse(BaseModel):
    id: int
    amount: Decimal
    payment_method: str
    paid_at: datetime | None
    print_request_id: int

    class Config:
        orm_mode = True
