from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# Load DATABASE_URL from .env file (required - no default for security)
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError(
        "DATABASE_URL not found in environment variables. "
        "Please set it in your .env file. "
        "Example: DATABASE_URL=postgresql+psycopg2://username:password@localhost:5432/mikrotik_billing"
    )

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database Models
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    plan_type = Column(String, nullable=False)  # 'daily_1000' or 'monthly_1000'
    expiry = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Auto-generated user tracking
    auto_generated = Column(Boolean, default=False)  # True if created via payment
    phone = Column(String, nullable=True)  # Customer phone number
    email = Column(String, nullable=True)  # Customer email (optional)
    buyer_name = Column(String, nullable=True)  # Customer name
    tx_ref = Column(String, nullable=True)  # ZenoPay transaction reference
    device_count = Column(Integer, default=1)  # Number of devices (1 or 2)

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    amount = Column(Float, nullable=False)
    date = Column(DateTime, default=datetime.utcnow)
    verified = Column(Boolean, default=True)

class PaymentTransaction(Base):
    __tablename__ = "payment_transactions"

    id = Column(Integer, primary_key=True, index=True)
    tx_ref = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, nullable=False)
    buyer_name = Column(String, nullable=False)
    plan_type = Column(String, nullable=False)
    device_count = Column(Integer, default=1)  # Number of devices (1 or 2)
    amount = Column(Float, nullable=False)
    payment_link = Column(String, nullable=False)
    status = Column(String, default="PENDING")  # PENDING, COMPLETED, FAILED
    user_id = Column(Integer, nullable=True)  # Set after user is created
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

class Log(Base):
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True, index=True)
    event = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
