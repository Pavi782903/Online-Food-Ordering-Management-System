# Online Food Ordering Management System

A FastAPI, SQLAlchemy ORM, and SQLite implementation for managing food, customers, and orders.

## Run the API

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload
```

Open Swagger UI at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

The SQLite database is created as `food_ordering.db` on first startup. The app automatically inserts three food records and three customer records when the tables are empty.

## API endpoints

- `POST /food`, `GET /food`, `GET /food/search`, `PUT /food/{food_id}`, `DELETE /food/{food_id}`
- `POST /customers`, `GET /customers`
- `POST /orders`, `GET /orders`, `GET /orders/search`, `PATCH /orders/{order_id}/status`, `DELETE /orders/{order_id}`

Order totals are calculated on the server from the current food price and requested quantity. Orders require an existing customer and available food.
