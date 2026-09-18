from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class FoodBase(BaseModel):
    food_name: str = Field(min_length=1, max_length=100)
    category: str = Field(min_length=1, max_length=50)
    price: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    availability: bool = True


class FoodCreate(FoodBase):
    pass


class FoodUpdate(BaseModel):
    food_name: str | None = Field(default=None, min_length=1, max_length=100)
    category: str | None = Field(default=None, min_length=1, max_length=50)
    price: Decimal | None = Field(default=None, gt=0, max_digits=10, decimal_places=2)
    availability: bool | None = None


class FoodResponse(FoodBase):
    model_config = ConfigDict(from_attributes=True)

    food_id: int


class CustomerBase(BaseModel):
    customer_name: str = Field(min_length=1, max_length=100)
    phone_number: str = Field(min_length=7, max_length=20)
    address: str = Field(min_length=1, max_length=255)


class CustomerCreate(CustomerBase):
    pass


class CustomerResponse(CustomerBase):
    model_config = ConfigDict(from_attributes=True)

    customer_id: int


class OrderCreate(BaseModel):
    customer_id: int = Field(gt=0)
    food_id: int = Field(gt=0)
    quantity: int = Field(gt=0, le=100)


class OrderStatusUpdate(BaseModel):
    order_status: Literal["Pending", "Preparing", "Ready", "Delivered", "Cancelled"]


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    order_id: int
    customer_id: int
    food_id: int
    quantity: int
    total_amount: Decimal
    order_status: str
