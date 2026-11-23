# Сириус.Еда — практические работы № 6–10

ЛР № 10: [изолированные тесты, нагрузка и CI](docs/lab10_defense.md).
Проверка: `python -m pytest tests/integration -v`. Нагрузочный стенд:
`python -m scripts.run_lab10_load --web`.

Для чистого компьютера начните с [инструкции запуска](docs/start_labs_6-9.md). Сценарии защиты:

| Работа | Что показать |
|---|---|
| [№ 6 — gRPC, 10 баллов](docs/lab6_defense.md) | Назначение, получение и завершение доставки; 503/504; поток статусов и двусторонний чат |
| [№ 7 — RabbitMQ, 10 баллов](docs/lab7_defense.md) | Два подписчика, повтор события, DLQ, Saga и Transactional Outbox |
| [№ 8 — SSR, 8 баллов](docs/lab8_defense.md) | Список и карточка в HTML, 404, загрузка и восстановление после отказа API |
| [№ 9 — наблюдаемость, 8 баллов](docs/lab9_defense.md) | Один correlation ID в разных процессах, Prometheus и пять панелей Grafana |

## ЛР № 6: архитектура доставки

```text
Браузер / Swagger → FastAPI (JWT, RBAC, HTTP)
                      → DeliveryGrpcClient (Protobuf поверх HTTP/2)
                          → delivery_server.py → DeliveryService → DeliveryRepository → PostgreSQL
```

HTTP-модуль доставки вызывает адаптер, а бизнес-правила и SQL выполняются в отдельном процессе. Схема `proto/delivery.proto` задаёт четыре unary RPC и два потоковых RPC. Монолит переводит недоступность в 503, дедлайн unary вызова — в 504. База в учебном проекте общая.

## ЛР № 7: архитектура событий

```text
POST /orders/{id}/pay
  → PostgreSQL [paid + outbox: order.paid] → Outbox worker (publisher)
  → RabbitMQ sirius_events (topic exchange)
      ├─ order.paid      → kitchen_queue  → Kitchen consumer  → kitchen_orders
      ├─ order.paid      → delivery_queue → Delivery consumer → deliveries или outbox: delivery.failed
      ├─ delivery.failed → payment_queue  → Payment consumer  → возврат + cancelled + outbox: order.cancelled
      └─ order.cancelled → kitchen_queue  → Kitchen consumer  → отмена записи кухни

Отклонённое сообщение → dlx_exchange (direct) → <consumer>_dlq
```

Деньги резервируются при создании заказа, как в исходном проекте. Оплата подтверждает резерв и записывает `order.paid` без повторного списания. Outbox отмечает публикацию по подтверждению брокера. Consumer фиксирует результат и ключ `(consumer, event_id)` вместе, затем отправляет ACK. Возможный повтор после сбоя между публикацией и отметкой не дублирует результат.

## ЛР № 8 и № 9

Next.js рендерит каталог и карточку на сервере, получая данные из FastAPI по REST. [Документация фронтенда](sirius-food-frontend/README.md) описывает маршруты и проверки.

FastAPI передаёт `X-Correlation-ID` через outbox и заголовок AMQP. Кухня, доставка и компенсация используют тот же ID в JSON-логах. Prometheus собирает HTTP-метрики, счётчики Redis и метрики очередей RabbitMQ; Grafana автоматически загружает источник и дашборд.
