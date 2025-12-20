import os
import secrets
import string
from datetime import datetime

from elusion.zenopay import Currency, ZenoPay
from elusion.zenopay.models.checkout import NewCheckout
from elusion.zenopay.utils import generate_id

# Load configuration from environment
ZENOPAY_API_KEY = os.getenv("ZENOPAY_API_KEY")
DAILY_1_DEVICE_PRICE = int(os.getenv("DAILY_1_DEVICE_PRICE", "1000"))
DAILY_2_DEVICES_PRICE = int(os.getenv("DAILY_2_DEVICES_PRICE", "1500"))
MONTHLY_1_DEVICE_PRICE = int(os.getenv("MONTHLY_1_DEVICE_PRICE", "10000"))
MONTHLY_2_DEVICES_PRICE = int(os.getenv("MONTHLY_2_DEVICES_PRICE", "15000"))
WEBHOOK_URL = os.getenv("ZENOPAY_WEBHOOK_URL", "")


class PaymentService:
    def __init__(self):
        self.client = ZenoPay(api_key=ZENOPAY_API_KEY)

    def generate_username(self, prefix="user"):
        """Generate a unique username"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_suffix = "".join(secrets.choice(string.digits) for _ in range(4))
        return f"{prefix}_{timestamp}_{random_suffix}"

    def generate_password(self, length=8):
        """Generate a secure random password"""
        characters = string.ascii_letters + string.digits
        return "".join(secrets.choice(characters) for _ in range(length))

    def get_plan_price(self, plan_type: str, device_count: int = 1) -> int:
        """Get price for a plan type and device count"""
        prices = {
            ("daily_1000", 1): DAILY_1_DEVICE_PRICE,
            ("daily_1000", 2): DAILY_2_DEVICES_PRICE,
            ("monthly_1000", 1): MONTHLY_1_DEVICE_PRICE,
            ("monthly_1000", 2): MONTHLY_2_DEVICES_PRICE,
        }
        return prices.get((plan_type, device_count), DAILY_1_DEVICE_PRICE)

    def create_payment_checkout(
        self, phone: str, buyer_name: str, plan_type: str, device_count: int = 1, redirect_url: str = None
    ):
        """
        Create a ZenoPay checkout session for internet access payment

        Args:
            phone: Customer phone number (e.g., "0781588379")
            buyer_name: Customer full name
            plan_type: "daily_1000" or "monthly_1000"
            device_count: Number of devices (1 or 2)
            redirect_url: URL to redirect after payment (optional)

        Returns:
            dict: {
                'payment_link': str,
                'tx_ref': str,
                'amount': int,
                'plan_type': str,
                'device_count': int
            }
        """
        amount = self.get_plan_price(plan_type, device_count)

        # Generate transaction reference
        tx_ref = generate_id()

        # Default redirect URL if not provided
        if not redirect_url:
            redirect_url = "https://your-domain.com/payment-success"

        # Create checkout session
        with self.client:
            checkout = NewCheckout(
                buyer_email=f"{phone}@temp.com",  # Temporary email (ZenoPay requires it)
                buyer_name=buyer_name,
                buyer_phone=phone,
                amount=amount,
                currency=Currency.TZS,
                redirect_url=redirect_url,
            )

            response = self.client.checkout.sync.create(checkout)

            return {
                "payment_link": response.results.payment_link,
                "tx_ref": response.results.tx_ref,
                "amount": amount,
                "plan_type": plan_type,
                "phone": phone,
                "buyer_name": buyer_name,
                "device_count": device_count,
            }

    def create_user_after_payment(
        self, tx_ref: str, phone: str, buyer_name: str, plan_type: str
    ):
        """
        Create MikroTik user with auto-generated credentials after successful payment

        Args:
            tx_ref: ZenoPay transaction reference
            phone: Customer phone number
            buyer_name: Customer name
            plan_type: "daily_1000" or "monthly_1000"

        Returns:
            dict: {
                'username': str,
                'password': str,
                'plan_type': str,
                'tx_ref': str
            }
        """
        # Generate credentials
        username = self.generate_username()
        password = self.generate_password()

        return {
            "username": username,
            "password": password,
            "plan_type": plan_type,
            "tx_ref": tx_ref,
            "phone": phone,
            "buyer_name": buyer_name,
        }


# Global instance
payment_service = PaymentService()
