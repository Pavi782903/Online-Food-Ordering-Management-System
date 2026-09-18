from contextlib import asynccontextmanager
from decimal import Decimal

from fastapi import Depends, FastAPI, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from database import Base, engine, get_db
from models import Customer, Food, Order
from schemas import (
    CustomerCreate,
    CustomerResponse,
    FoodCreate,
    FoodResponse,
    FoodUpdate,
    OrderCreate,
    OrderResponse,
    OrderStatusUpdate,
)


SEED_FOOD = (
    {"food_name": "Margherita Pizza", "category": "Pizza", "price": Decimal("12.50"), "availability": True},
    {"food_name": "Veggie Burger", "category": "Burgers", "price": Decimal("9.75"), "availability": True},
    {"food_name": "Chocolate Brownie", "category": "Dessert", "price": Decimal("5.25"), "availability": True},
)
SEED_CUSTOMERS = (
    {"customer_name": "Aarav Sharma", "phone_number": "9000000001", "address": "12 Lake Road"},
    {"customer_name": "Mia Wilson", "phone_number": "9000000002", "address": "45 Green Street"},
    {"customer_name": "Noah Brown", "phone_number": "9000000003", "address": "8 Market Avenue"},
)


def seed_database() -> None:
    with next(get_db()) as db:
        if db.scalar(select(Food).limit(1)) is None:
            db.add_all([Food(**food) for food in SEED_FOOD])
        if db.scalar(select(Customer).limit(1)) is None:
            db.add_all([Customer(**customer) for customer in SEED_CUSTOMERS])
        db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    seed_database()
    yield


app = FastAPI(
    title="Online Food Ordering Management System",
    description="CRUD APIs for food, customers, and orders. Use /docs to test with Swagger UI.",
    version="1.0.0",
    lifespan=lifespan,
)


def get_or_404(db: Session, model, item_id: int, label: str):
    item = db.get(model, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail=f"{label} with ID {item_id} not found")
    return item


@app.get("/", tags=["System"])
def root():
    return {"message": "Online Food Ordering Management System API", "swagger_ui": "/docs"}


@app.post("/food", response_model=FoodResponse, status_code=status.HTTP_201_CREATED, tags=["Food"])
def add_food(food: FoodCreate, db: Session = Depends(get_db)):
    try:
        item = Food(**food.model_dump())
        db.add(item)
        db.commit()
        db.refresh(item)
        return item
    except SQLAlchemyError as error:
        db.rollback()
        raise HTTPException(status_code=500, detail="Could not add food") from error


@app.get("/food", response_model=list[FoodResponse], tags=["Food"])
def view_all_food(
    category: str | None = Query(default=None),
    available_only: bool = Query(default=False),
    db: Session = Depends(get_db),
):
    query = select(Food).order_by(Food.food_id)
    if category:
        query = query.where(Food.category.ilike(f"%{category}%"))
    if available_only:
        query = query.where(Food.availability.is_(True))
    return db.scalars(query).all()


@app.get("/food/search", response_model=list[FoodResponse], tags=["Food"])
def search_food(
    name: str | None = Query(default=None, min_length=1),
    category: str | None = Query(default=None, min_length=1),
    db: Session = Depends(get_db),
):
    if not name and not category:
        raise HTTPException(status_code=400, detail="Provide name or category to search")
    query = select(Food)
    if name:
        query = query.where(Food.food_name.ilike(f"%{name}%"))
    if category:
        query = query.where(Food.category.ilike(f"%{category}%"))
    return db.scalars(query.order_by(Food.food_id)).all()


@app.put("/food/{food_id}", response_model=FoodResponse, tags=["Food"])
def update_food(food_id: int, food: FoodUpdate, db: Session = Depends(get_db)):
    item = get_or_404(db, Food, food_id, "Food")
    for key, value in food.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    try:
        db.commit()
        db.refresh(item)
        return item
    except SQLAlchemyError as error:
        db.rollback()
        raise HTTPException(status_code=500, detail="Could not update food") from error


@app.delete("/food/{food_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Food"])
def delete_food(food_id: int, db: Session = Depends(get_db)):
    item = get_or_404(db, Food, food_id, "Food")
    if db.scalar(select(Order).where(Order.food_id == food_id).limit(1)):
        raise HTTPException(status_code=409, detail="Food cannot be deleted because it has orders")
    try:
        db.delete(item)
        db.commit()
    except SQLAlchemyError as error:
        db.rollback()
        raise HTTPException(status_code=500, detail="Could not delete food") from error


@app.post("/customers", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED, tags=["Customers"])
def add_customer(customer: CustomerCreate, db: Session = Depends(get_db)):
    try:
        item = Customer(**customer.model_dump())
        db.add(item)
        db.commit()
        db.refresh(item)
        return item
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status_code=409, detail="Phone number is already registered") from error
    except SQLAlchemyError as error:
        db.rollback()
        raise HTTPException(status_code=500, detail="Could not add customer") from error


@app.get("/customers", response_model=list[CustomerResponse], tags=["Customers"])
def view_customers(db: Session = Depends(get_db)):
    return db.scalars(select(Customer).order_by(Customer.customer_id)).all()


@app.post("/orders", response_model=OrderResponse, status_code=status.HTTP_201_CREATED, tags=["Orders"])
def place_order(order: OrderCreate, db: Session = Depends(get_db)):
    customer = db.get(Customer, order.customer_id)
    if customer is None:
        raise HTTPException(status_code=404, detail=f"Customer with ID {order.customer_id} not found")
    food = db.get(Food, order.food_id)
    if food is None:
        raise HTTPException(status_code=404, detail=f"Food with ID {order.food_id} not found")
    if not food.availability:
        raise HTTPException(status_code=409, detail="Selected food is currently unavailable")

    item = Order(
        customer_id=customer.customer_id,
        food_id=food.food_id,
        quantity=order.quantity,
        total_amount=food.price * order.quantity,
        order_status="Pending",
    )
    try:
        db.add(item)
        db.commit()
        db.refresh(item)
        return item
    except SQLAlchemyError as error:
        db.rollback()
        raise HTTPException(status_code=500, detail="Could not place order") from error


@app.get("/orders", response_model=list[OrderResponse], tags=["Orders"])
def view_orders(db: Session = Depends(get_db)):
    return db.scalars(select(Order).order_by(Order.order_id)).all()


@app.get("/orders/search", response_model=list[OrderResponse], tags=["Orders"])
def search_orders(
    customer_id: int | None = Query(default=None, gt=0),
    order_status: str | None = Query(default=None, min_length=1),
    db: Session = Depends(get_db),
):
    if customer_id is None and order_status is None:
        raise HTTPException(status_code=400, detail="Provide customer_id or order_status to search")
    query = select(Order)
    if customer_id is not None:
        query = query.where(Order.customer_id == customer_id)
    if order_status:
        query = query.where(Order.order_status.ilike(order_status))
    return db.scalars(query.order_by(Order.order_id)).all()


@app.patch("/orders/{order_id}/status", response_model=OrderResponse, tags=["Orders"])
def update_order_status(order_id: int, update: OrderStatusUpdate, db: Session = Depends(get_db)):
    item = get_or_404(db, Order, order_id, "Order")
    item.order_status = update.order_status
    try:
        db.commit()
        db.refresh(item)
        return item
    except SQLAlchemyError as error:
        db.rollback()
        raise HTTPException(status_code=500, detail="Could not update order status") from error


@app.delete("/orders/{order_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Orders"])
def delete_order(order_id: int, db: Session = Depends(get_db)):
    item = get_or_404(db, Order, order_id, "Order")
    try:
        db.delete(item)
        db.commit()
    except SQLAlchemyError as error:
        db.rollback()
        raise HTTPException(status_code=500, detail="Could not delete order") from error
