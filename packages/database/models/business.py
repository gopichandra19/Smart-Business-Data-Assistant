"""Database models for business data entities."""

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Date, Text, ForeignKey, Enum as SAEnum
)
from sqlalchemy.orm import relationship
from packages.database.connection import Base
from datetime import datetime
import enum


class CustomerStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    CHURNED = "churned"


class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    RETURNED = "returned"


class PaymentMethod(str, enum.Enum):
    CREDIT_CARD = "credit_card"
    BANK_TRANSFER = "bank_transfer"
    CHECK = "check"
    WIRE = "wire"


class Customer(Base):
    __tablename__ = "customers"

    customer_id = Column(Integer, primary_key=True, autoincrement=True)
    customer_name = Column(String(200), nullable=False, index=True)
    region = Column(String(50), nullable=False, index=True)
    segment = Column(String(50), nullable=False, index=True)
    industry = Column(String(100), nullable=False)
    email = Column(String(200))  # Restricted field
    phone = Column(String(50))  # Restricted field
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20), default=CustomerStatus.ACTIVE.value)

    orders = relationship("Order", back_populates="customer")


class Product(Base):
    __tablename__ = "products"

    product_id = Column(Integer, primary_key=True, autoincrement=True)
    product_name = Column(String(200), nullable=False, index=True)
    category = Column(String(100), nullable=False, index=True)
    unit_price = Column(Float, nullable=False)
    cost = Column(Float, nullable=False)

    orders = relationship("Order", back_populates="product")


class Salesperson(Base):
    __tablename__ = "salespeople"

    salesperson_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    region = Column(String(50), nullable=False, index=True)
    team = Column(String(100), nullable=False)
    salary = Column(Float)  # Restricted field

    orders = relationship("Order", back_populates="salesperson")


class Order(Base):
    __tablename__ = "orders"

    order_id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey("customers.customer_id"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.product_id"), nullable=False, index=True)
    salesperson_id = Column(Integer, ForeignKey("salespeople.salesperson_id"), nullable=False, index=True)
    order_date = Column(Date, nullable=False, index=True)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    discount = Column(Float, default=0.0)
    status = Column(String(20), default=OrderStatus.PENDING.value)

    customer = relationship("Customer", back_populates="orders")
    product = relationship("Product", back_populates="orders")
    salesperson = relationship("Salesperson", back_populates="orders")
    transactions = relationship("Transaction", back_populates="order")


class Transaction(Base):
    __tablename__ = "transactions"

    transaction_id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.order_id"), nullable=False, index=True)
    transaction_date = Column(Date, nullable=False, index=True)
    revenue = Column(Float, nullable=False)
    cost = Column(Float, nullable=False)
    profit = Column(Float, nullable=False)
    payment_method = Column(String(30), default=PaymentMethod.CREDIT_CARD.value)

    order = relationship("Order", back_populates="transactions")


class Campaign(Base):
    __tablename__ = "campaigns"

    campaign_id = Column(Integer, primary_key=True, autoincrement=True)
    campaign_name = Column(String(200), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    region = Column(String(50), nullable=False, index=True)
    segment = Column(String(50), nullable=False)
    spend = Column(Float, nullable=False)
