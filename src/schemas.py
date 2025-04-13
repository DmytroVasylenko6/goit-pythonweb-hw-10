import re
from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, validator


class ContactModel(BaseModel):
    name: str = Field(min_length=2, max_length=50, example="John")
    surname: str = Field(min_length=2, max_length=50, example="Doe")
    email: EmailStr = Field(
        min_length=7, max_length=100, example="john.doe@example.com"
    )
    phone: str = Field(min_length=7, max_length=20, example="+380501234567")
    birthday: date = Field(example="1990-01-01")
    info: Optional[str] = Field(None, max_length=500, example="Additional info")
    user_id: int = Field(example=1)

    @validator("phone")
    def validate_phone(cls, value):
        phone_regex = r"^\+?[1-9]\d{1,14}$"
        if not re.match(phone_regex, value):
            raise ValueError(
                "Phone number must be in international format (e.g., +380501234567)"
            )
        return value

    @validator("birthday")
    def validate_birthday(cls, value):
        if value > date.today():
            raise ValueError("Birthday cannot be in the future")
        return value


class ContactResponse(ContactModel):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]
    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50, example="john_doe")
    email: EmailStr
    password: str = Field(min_length=6)


class User(BaseModel):
    id: int
    username: str
    email: EmailStr
    is_verified: bool
    avatar_url: Optional[str]
    contacts: List[ContactResponse] = []
    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    email: Optional[str] = None


class RequestEmail(BaseModel):
    email: EmailStr
