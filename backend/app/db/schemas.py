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
