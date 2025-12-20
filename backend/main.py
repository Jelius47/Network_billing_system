import os
from datetime import datetime, timedelta
from typing import List, Optional

import uvicorn
from apscheduler.schedulers.background import BackgroundScheduler
from database import Log, Payment, PaymentTransaction, User, get_db, init_db
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from mikrotik_api import mikrotik
from payment_service import payment_service
from whatsapp_service import whatsapp_service
from pydantic import BaseModel
from sqlalchemy.orm import Session

load_dotenv()
API_PORT = int(os.getenv("API_PORT", 8004))
app = FastAPI(title="MikroTik Billing System")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic Models
class UserCreate(BaseModel):
    username: str
    password: str
    plan_type: str  # 'daily_1000' or 'monthly_1000'


class UserResponse(BaseModel):
    id: int
    username: str
    plan_type: str
    expiry: datetime
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class PaymentCreate(BaseModel):
    user_id: int
    amount: float


class PaymentResponse(BaseModel):
    id: int
    user_id: int
    amount: float
    date: datetime
    verified: bool

    class Config:
        from_attributes = True


class ExtendSubscription(BaseModel):
    days: int


class PaymentCheckoutRequest(BaseModel):
    phone: str  # e.g., "0781588379"
    buyer_name: str  # Customer full name
    plan_type: str  # 'daily_1000' or 'monthly_1000'
    device_count: int = 1  # Number of devices (1 or 2)
    redirect_url: Optional[str] = None


class PaymentCheckoutResponse(BaseModel):
    payment_link: str
    tx_ref: str
    amount: int
    plan_type: str


class WebhookPayload(BaseModel):
    order_id: Optional[str] = None
    payment_status: str
    reference: Optional[str] = None


# Utility Functions
def calculate_expiry(plan_type: str) -> datetime:
    """Calculate expiry date based on plan type"""
    now = datetime.utcnow()
    if plan_type == "daily_1000":
        return now + timedelta(days=1)
    elif plan_type == "monthly_1000":
        return now + timedelta(days=30)
    else:
        raise ValueError(f"Invalid plan type: {plan_type}")


def log_event(db: Session, event: str):
    """Log an event to the database"""
    log = Log(event=event)
    db.add(log)
    db.commit()


# Background Task for Auto-Disabling Expired Users
def check_expired_users():
    """Check and disable expired users"""
    db = next(get_db())
    try:
        now = datetime.utcnow()
        expired_users = (
            db.query(User).filter(User.expiry < now, User.is_active == True).all()
        )

        for user in expired_users:
            # Disable in MikroTik
            success = mikrotik.disable_user(user.username)
            if success:
                # Update database
                user.is_active = False
                db.commit()
                log_event(db, f"Auto-disabled expired user: {user.username}")
                print(f"Disabled expired user: {user.username}")
    except Exception as e:
        print(f"Error checking expired users: {e}")
    finally:
        db.close()


# Initialize Scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(check_expired_users, "interval", minutes=10)
scheduler.start()


# API Endpoints
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    # Refresh MikroTik config from .env (clears any IP caches)
    mikrotik.refresh_config()

    init_db()
    print("Database initialized")

    # Try to connect to MikroTik (non-blocking)
    try:
        import socket

        # Set default socket timeout
        socket.setdefaulttimeout(5)

        if mikrotik.connect():
            print("MikroTik connected successfully")
        else:
            print("Warning: MikroTik connection failed - will retry on first API call")
    except Exception as e:
        print(f"Warning: MikroTik connection failed: {e}")
        print("System will continue - connection will retry on API calls")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    mikrotik.disconnect()
    scheduler.shutdown()


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "online", "message": "MikroTik Billing System API"}


@app.post("/users", response_model=UserResponse)
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Create a new user in database and MikroTik"""
    # Check if username already exists
    existing_user = db.query(User).filter(User.username == user.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")

    # Calculate expiry
    expiry = calculate_expiry(user.plan_type)

    # Create in MikroTik first
    success = mikrotik.create_user(user.username, user.password, user.plan_type)
    if not success:
        log_event(db, f"Failed to create user in MikroTik: {user.username}")
        raise HTTPException(status_code=500, detail="Failed to create user in MikroTik")

    # Create in database
    db_user = User(
        username=user.username,
        password=user.password,
        plan_type=user.plan_type,
        expiry=expiry,
        is_active=True,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    log_event(db, f"Created user: {user.username}")
    return db_user


@app.get("/users", response_model=List[UserResponse])
async def list_users(db: Session = Depends(get_db)):
    """List all users"""
    users = db.query(User).all()
    return users


@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: Session = Depends(get_db)):
    """Get a specific user"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.post("/users/{user_id}/extend")
async def extend_user(
    user_id: int, extension: ExtendSubscription, db: Session = Depends(get_db)
):
    """Extend user subscription"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Extend expiry
    user.expiry = user.expiry + timedelta(days=extension.days)

    # Enable user if disabled
    if not user.is_active:
        success = mikrotik.enable_user(user.username)
        if success:
            user.is_active = True

    db.commit()
    log_event(db, f"Extended user {user.username} by {extension.days} days")

    return {
        "message": f"User extended by {extension.days} days",
        "new_expiry": user.expiry,
    }


@app.post("/users/{user_id}/toggle")
async def toggle_user(user_id: int, db: Session = Depends(get_db)):
    """Toggle user active status"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.is_active:
        success = mikrotik.disable_user(user.username)
        if success:
            user.is_active = False
    else:
        success = mikrotik.enable_user(user.username)
        if success:
            user.is_active = True

    db.commit()
    log_event(
        db,
        f"Toggled user {user.username} to {'active' if user.is_active else 'inactive'}",
    )

    return {"message": "User toggled", "is_active": user.is_active}


@app.delete("/users/{user_id}")
async def delete_user(user_id: int, db: Session = Depends(get_db)):
    """Delete user from both MikroTik and database"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    username = user.username
    mikrotik_deleted = False
    warning_message = None

    # Try to delete from MikroTik first
    try:
        mikrotik_deleted = mikrotik.delete_user(username)
        if not mikrotik_deleted:
            warning_message = "Could not delete from MikroTik (connection issue or user not found in router)"
    except Exception as e:
        warning_message = f"MikroTik deletion failed: {str(e)}"
        print(f"MikroTik error during delete: {e}")

    # Always delete from database (even if MikroTik fails)
    db.delete(user)
    db.commit()
    log_event(
        db,
        f"Deleted user {username} from database. MikroTik status: {'success' if mikrotik_deleted else 'failed'}",
    )

    # Return appropriate message
    if mikrotik_deleted:
        return {
            "message": f"User {username} deleted successfully from both MikroTik and database",
            "success": True,
        }
    else:
        return {
            "message": f"User {username} deleted from database. {warning_message}. You may need to manually remove from MikroTik if it still exists.",
            "success": True,
            "warning": warning_message,
        }


@app.post("/payments", response_model=PaymentResponse)
async def record_payment(payment: PaymentCreate, db: Session = Depends(get_db)):
    """Record a payment"""
    # Verify user exists
    user = db.query(User).filter(User.id == payment.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Create payment record
    db_payment = Payment(user_id=payment.user_id, amount=payment.amount, verified=True)
    db.add(db_payment)
    db.commit()
    db.refresh(db_payment)

    log_event(db, f"Payment recorded for user ID {payment.user_id}: ${payment.amount}")
    return db_payment


@app.get("/payments", response_model=List[PaymentResponse])
async def list_payments(db: Session = Depends(get_db)):
    """List all payments"""
    payments = db.query(Payment).all()
    return payments


@app.get("/expired")
async def list_expired(db: Session = Depends(get_db)):
    """List all expired users"""
    now = datetime.utcnow()
    expired_users = db.query(User).filter(User.expiry < now).all()
    return expired_users


@app.get("/active-connections")
async def get_active_connections():
    """Get currently active connections from MikroTik"""
    active_users = mikrotik.get_active_users()
    return {"count": len(active_users), "users": active_users}


@app.get("/stats")
async def get_stats(db: Session = Depends(get_db)):
    """Get system statistics"""
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    expired_users = db.query(User).filter(User.expiry < datetime.utcnow()).count()
    total_payments = db.query(Payment).count()

    return {
        "total_users": total_users,
        "active_users": active_users,
        "expired_users": expired_users,
        "total_payments": total_payments,
    }


@app.post("/sync-users")
async def sync_users(db: Session = Depends(get_db)):
    """Sync database users with MikroTik - remove stale users not in MikroTik"""
    try:
        # Get all users from MikroTik
        mikrotik_usernames = set(mikrotik.get_all_users())

        if not mikrotik_usernames:
            return {
                "success": False,
                "message": "Failed to get users from MikroTik",
                "removed": 0,
            }

        # Get all users from database
        db_users = db.query(User).all()

        # Find stale users (in database but not in MikroTik)
        stale_users = []
        for user in db_users:
            if user.username not in mikrotik_usernames:
                stale_users.append(user.username)

        # Remove stale users
        removed_count = 0
        for username in stale_users:
            user = db.query(User).filter(User.username == username).first()
            if user:
                db.delete(user)
                removed_count += 1
                log_event(db, f"Removed stale user {username} during sync")

        db.commit()

        return {
            "success": True,
            "message": f"Sync completed. Removed {removed_count} stale users.",
            "removed": removed_count,
            "stale_users": stale_users,
            "mikrotik_total": len(mikrotik_usernames),
            "database_total": len(db_users) - removed_count,
        }
    except Exception as e:
        return {"success": False, "message": f"Sync failed: {str(e)}", "removed": 0}


# ==================== PAYMENT ENDPOINTS ====================


@app.post("/payments/create-checkout", response_model=PaymentCheckoutResponse)
async def create_payment_checkout(
    request: PaymentCheckoutRequest, db: Session = Depends(get_db)
):
    """
    Create a ZenoPay checkout session for internet access payment
    """
    try:
        # Create checkout with ZenoPay
        checkout_data = payment_service.create_payment_checkout(
            phone=request.phone,
            buyer_name=request.buyer_name,
            plan_type=request.plan_type,
            device_count=request.device_count,
            redirect_url=request.redirect_url,
        )

        # Save transaction to database
        transaction = PaymentTransaction(
            tx_ref=checkout_data["tx_ref"],
            phone=request.phone,
            buyer_name=request.buyer_name,
            plan_type=request.plan_type,
            device_count=request.device_count,
            amount=checkout_data["amount"],
            payment_link=checkout_data["payment_link"],
            status="PENDING",
        )
        db.add(transaction)
        db.commit()

        log_event(db, f"Payment checkout created: {checkout_data['tx_ref']}")

        # Send payment link via WhatsApp
        try:
            whatsapp_result = whatsapp_service.send_payment_reminder(
                phone=request.phone,
                buyer_name=request.buyer_name,
                payment_link=checkout_data["payment_link"],
            )

            if whatsapp_result["success"]:
                log_event(
                    db,
                    f"WhatsApp payment reminder sent to {request.phone} - Message ID: {whatsapp_result.get('message_id')}",
                )
            else:
                log_event(
                    db,
                    f"WhatsApp payment reminder failed for {request.phone}: {whatsapp_result.get('error')}",
                )
                print(f"WhatsApp payment reminder error: {whatsapp_result.get('error')}")

        except Exception as e:
            log_event(db, f"WhatsApp payment reminder exception: {str(e)}")
            print(f"WhatsApp payment reminder exception: {e}")

        return PaymentCheckoutResponse(**checkout_data)

    except Exception as e:
        log_event(db, f"Payment checkout failed: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to create payment checkout: {str(e)}"
        )


@app.post("/payments/webhook")
async def payment_webhook(request: Request, db: Session = Depends(get_db)):
    """
    ZenoPay webhook endpoint for payment notifications
    """
    try:
        # Get raw body
        raw_body = await request.body()
        body_str = raw_body.decode("utf-8")

        # Parse JSON
        import json

        payload = json.loads(body_str)

        print(f"Received webhook: {payload}")

        # Extract payment data (adjust based on ZenoPay webhook format)
        payment_status = payload.get("payment_status", "").upper()
        tx_ref = payload.get("reference") or payload.get("tx_ref")

        if not tx_ref:
            return {"status": "error", "message": "No transaction reference found"}

        # Find transaction in database
        transaction = (
            db.query(PaymentTransaction).filter(PaymentTransaction.tx_ref == tx_ref).first()
        )

        if not transaction:
            return {
                "status": "error",
                "message": f"Transaction not found: {tx_ref}",
            }

        # Handle payment status
        if payment_status == "COMPLETED" and transaction.status != "COMPLETED":
            # Create user with auto-generated credentials
            user_data = payment_service.create_user_after_payment(
                tx_ref=tx_ref,
                phone=transaction.phone,
                buyer_name=transaction.buyer_name,
                plan_type=transaction.plan_type,
            )

            # Calculate expiry
            expiry = calculate_expiry(transaction.plan_type)

            # Create user in MikroTik
            success = mikrotik.create_user(
                user_data["username"], user_data["password"], transaction.plan_type
            )

            if not success:
                log_event(db, f"Failed to create MikroTik user for payment: {tx_ref}")
                return {
                    "status": "error",
                    "message": "Failed to create user in MikroTik",
                }

            # Create user in database
            db_user = User(
                username=user_data["username"],
                password=user_data["password"],
                plan_type=transaction.plan_type,
                expiry=expiry,
                is_active=True,
                auto_generated=True,
                phone=transaction.phone,
                buyer_name=transaction.buyer_name,
                tx_ref=tx_ref,
                device_count=transaction.device_count,
            )
            db.add(db_user)
            db.commit()
            db.refresh(db_user)

            # Update transaction status
            transaction.status = "COMPLETED"
            transaction.user_id = db_user.id
            transaction.completed_at = datetime.utcnow()
            db.commit()

            log_event(
                db,
                f"Payment completed: {tx_ref} - User {user_data['username']} created",
            )

            # Send credentials via WhatsApp
            try:
                whatsapp_result = whatsapp_service.send_credentials_message(
                    phone=transaction.phone,
                    username=user_data["username"],
                    password=user_data["password"],
                    plan_type=transaction.plan_type,
                    buyer_name=transaction.buyer_name,
                )

                if whatsapp_result["success"]:
                    log_event(
                        db,
                        f"WhatsApp credentials sent to {transaction.phone} - Message ID: {whatsapp_result.get('message_id')}",
                    )
                else:
                    log_event(
                        db,
                        f"WhatsApp send failed for {transaction.phone}: {whatsapp_result.get('error')}",
                    )
                    print(f"WhatsApp error: {whatsapp_result.get('error')}")

            except Exception as e:
                log_event(db, f"WhatsApp service error: {str(e)}")
                print(f"WhatsApp exception: {e}")

            return {
                "status": "success",
                "message": "User created successfully",
                "username": user_data["username"],
                "password": user_data["password"],
            }

        elif payment_status == "FAILED":
            transaction.status = "FAILED"
            db.commit()
            log_event(db, f"Payment failed: {tx_ref}")
            return {"status": "acknowledged", "message": "Payment failed"}

        return {"status": "acknowledged"}

    except Exception as e:
        print(f"Webhook error: {e}")
        log_event(db, f"Webhook error: {str(e)}")
        return {"status": "error", "message": str(e)}


@app.get("/payments/transactions")
async def list_payment_transactions(db: Session = Depends(get_db)):
    """List all payment transactions"""
    transactions = db.query(PaymentTransaction).order_by(
        PaymentTransaction.created_at.desc()
    ).all()
    return transactions


@app.get("/payments/check/{tx_ref}")
async def check_payment_status(tx_ref: str, db: Session = Depends(get_db)):
    """Check payment status and return credentials if completed"""
    transaction = (
        db.query(PaymentTransaction).filter(PaymentTransaction.tx_ref == tx_ref).first()
    )

    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    if transaction.status == "COMPLETED" and transaction.user_id:
        user = db.query(User).filter(User.id == transaction.user_id).first()
        if user:
            return {
                "status": "COMPLETED",
                "username": user.username,
                "password": user.password,
                "plan_type": user.plan_type,
                "expiry": user.expiry,
            }

    return {
        "status": transaction.status,
        "message": "Payment not yet completed",
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=API_PORT)
