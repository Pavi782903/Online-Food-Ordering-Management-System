from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class Food(Base):
    __tablename__ = "food"

    food_id: Mapped[int] = mapped_column(primary_key=True, index=True)
    food_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    availability: Mapped[bool] = mapped_column(default=True, nullable=False)

    orders: Mapped[list["Order"]] = relationship(back_populates="food")


class Customer(Base):
    __tablename__ = "customer"

    customer_id: Mapped[int] = mapped_column(primary_key=True, index=True)
    customer_name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    address: Mapped[str] = mapped_column(String(255), nullable=False)

    orders: Mapped[list["Order"]] = relationship(
        back_populates="customer", cascade="all, delete-orphan"
    )


class Order(Base):
    __tablename__ = "orders"

    order_id: Mapped[int] = mapped_column(primary_key=True, index=True)
    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customer.customer_id"), nullable=False, index=True
    )
    food_id: Mapped[int] = mapped_column(
        ForeignKey("food.food_id"), nullable=False, index=True
    )
    quantity: Mapped[int] = mapped_column(nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    order_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="Pending", index=True
    )

    customer: Mapped[Customer] = relationship(back_populates="orders")
    food: Mapped[Food] = relationship(back_populates="orders")
