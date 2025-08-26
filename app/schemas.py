from datetime import datetime
from pydantic import BaseModel, validator, ValidationError

class UserCreate(BaseModel):
    username: str
    password: str

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Пароль має містити мінімум 8 символів')
        return v

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    registered_at: datetime  

    class Config:
        from_attributes = True  
class PasswordChange(BaseModel):
    old_password: str
    new_password: str