from sqlalchemy import text


def test_payment_without_token_is_rejected(client, db):
    response = client.post("/orders/999999/pay")

    assert response.status_code == 401
    assert db.execute(text("SELECT count(*) FROM outbox")).scalar_one() == 0
