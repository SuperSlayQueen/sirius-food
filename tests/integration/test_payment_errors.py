"""Оплата отсутствующего заказа не должна создавать записи или события."""
from sqlalchemy import text


def test_missing_order_payment_creates_no_event(client, db, seed):
    account = seed()

    response = client.post(
        "/orders/999999/pay",
        headers=account["headers"],
    )

    assert response.status_code == 404
    assert db.execute(text("SELECT count(*) FROM outbox")).scalar_one() == 0
    assert db.execute(text("SELECT count(*) FROM orders")).scalar_one() == 0
