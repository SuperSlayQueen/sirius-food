"""
Pydantic-схемы для валидации входных и выходных данных.

ВАЖНО: в OrderCreate больше нет user_id — идентификатор пользователя
берётся сервером из JWT, а не доверяется клиенту (защита от подмены).
"""
from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    # Пароль обязателен с лабораторной № 3: хешируется bcrypt-ом.
    password: str = Field(min_length=6)
    phone: str | None = None


class UserResponse(BaseModel):
    id: int
    email: str
    balance: float

    class Config:
        from_attributes = True


class MenuItemCreate(BaseModel):
    name: str
    price: float
    category_id: int | None = None


class MenuItemUpdate(BaseModel):
    name: str | None = None
    price: float | None = None
    is_available: bool | None = None
    category_id: int | None = None


class OrderCreate(BaseModel):
    # user_id удалён: сервер определяет пользователя из JWT.
    item_id: int
    quantity: int


class DeliveryAssign(BaseModel):
    order_id: int
    courier_id: int
