"""
Определение ORM-моделей предметной области «Сириус.Еда».
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False)
    phone = Column(String, nullable=True)
    balance = Column(Float, default=0.0)
    is_blocked = Column(Boolean, default=False)
    # bcrypt-хеш пароля. В открытом виде пароль нигде не хранится.
    password_hash = Column(String, nullable=False)
    # Роль пользователя (RBAC): student / cook / courier / admin.
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False, index=True)

    role = relationship("Role")


class Role(Base):
    """Роль пользователя: student, cook, courier, admin."""
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)


class RefreshToken(Base):
    """
    Refresh-токен для обновления access-токена.

    Храним SHA-256-хеш токена, а не сам токен: при утечке БД
    злоумышленник не получит действующие токены.
    """
    __tablename__ = "refresh_tokens"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token_hash = Column(String, unique=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    is_revoked = Column(Boolean, default=False)

    user = relationship("User")


class MenuCategory(Base):
    """Категория меню (кешируется с ключом menu:category:{id})."""
    __tablename__ = "menu_categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)


class MenuItem(Base):
    __tablename__ = "menu_items"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    is_available = Column(Boolean, default=True)
    # Категория необязательна: блюдо без категории видно в общем меню.
    category_id = Column(Integer, ForeignKey("menu_categories.id"), nullable=True)
    category = relationship("MenuCategory")


class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    item_id = Column(Integer, ForeignKey("menu_items.id"))
    quantity = Column(Integer, nullable=False)
    # Сумма, зарезервированная при создании; цена меню может измениться.
    charged_amount = Column(Float, nullable=True)
    status = Column(String, default="processing")
    user = relationship("User")
    item = relationship("MenuItem")


class Delivery(Base):
    __tablename__ = "deliveries"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    courier_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    status = Column(String, default="pending")
    order = relationship("Order")
    courier = relationship("User")


class KitchenOrder(Base):
    __tablename__ = "kitchen_orders"
    order_id = Column(Integer, ForeignKey("orders.id"), primary_key=True)
    status = Column(String, nullable=False)


class ProcessedEvent(Base):
    __tablename__ = "processed_events"
    consumer = Column(String(32), primary_key=True)
    event_id = Column(String(36), primary_key=True)


class OutboxEvent(Base):
    __tablename__ = "outbox"
    id = Column(Integer, primary_key=True)
    routing_key = Column(String(40), nullable=False)
    payload = Column(JSON, nullable=False)
    correlation_id = Column(String(128), nullable=False)
    published_at = Column(DateTime(timezone=True), index=True)
