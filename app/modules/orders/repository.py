"""
Инфраструктурный слой модуля orders (Круг 3: Interface Adapters).

Единственный файл модуля, который знает о SQLAlchemy и о структуре
таблиц базы данных.
"""
from sqlalchemy.orm import Session

from app.models import KitchenOrder, MenuItem, Order, OutboxEvent, User


class OrderRepository:
    """
    Класс отвечает исключительно за выполнение операций ввода-вывода
    в контексте СУБД PostgreSQL с использованием SQLAlchemy ORM.
    Бизнес-правила в данном классе отсутствуют.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_user_by_id(self, user_id: int):
        """Извлечение объекта пользователя по идентификатору."""
        return (
            self.db.query(User).filter(User.id == user_id)
            .with_for_update().populate_existing().first()
        )

    def get_menu_item_by_id(self, item_id: int):
        """Извлечение объекта блюда из меню по идентификатору."""
        return self.db.query(MenuItem).filter(MenuItem.id == item_id).first()

    def update_user_balance(self, user, new_balance: float) -> None:
        """
        Изменение значения баланса пользователя.

        Транзакция НЕ фиксируется здесь: изменение баланса и создание заказа
        должны попасть в БД атомарно (как в MVP-версии, где был один commit).
        Фиксация выполняется в save_order().
        """
        user.balance = new_balance
        self.db.add(user)

    def save_order(self, user_id: int, item_id: int, quantity: int, charged_amount: float) -> int:
        """
        Создание новой записи заказа и фиксация транзакции
        (вместе с ранее изменённым балансом пользователя).
        Возвращает идентификатор созданного заказа.
        """
        new_order = Order(
            user_id=user_id,
            item_id=item_id,
            quantity=quantity,
            charged_amount=charged_amount,
            status="processing",
        )
        self.db.add(new_order)
        self.db.commit()
        self.db.refresh(new_order)
        return new_order.id

    def get_order(self, order_id: int):
        """Извлечение заказа по идентификатору."""
        return self.db.query(Order).filter(Order.id == order_id).with_for_update().first()

    def save_payment(self, order, routing_key: str, payload: dict, correlation_id: str) -> None:
        order.status = "paid"
        self.db.add(OutboxEvent(routing_key=routing_key, payload=payload, correlation_id=correlation_id))
        self.db.commit()

    def set_order_status(self, order, status: str) -> None:
        """Сохранение нового статуса заказа."""
        order.status = status
        self.db.add(order)
        self.db.commit()

    def list_kitchen_orders(self) -> list[tuple]:
        return (
            self.db.query(Order, KitchenOrder.status)
            .join(KitchenOrder, KitchenOrder.order_id == Order.id)
            .filter(KitchenOrder.status == "pending", Order.status == "paid")
            .order_by(Order.id)
            .all()
        )
