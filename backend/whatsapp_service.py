import os
import requests
from dotenv import load_dotenv

load_dotenv()

# WhatsApp Business API Configuration
WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
WHATSAPP_BUSINESS_ID = os.getenv("WHATSAPP_BUSINESS_ID")
WHATSAPP_API_VERSION = os.getenv("WHATSAPP_API_VERSION", "v21.0")


class WhatsAppService:
    def __init__(self):
        self.access_token = WHATSAPP_ACCESS_TOKEN
        self.phone_number_id = WHATSAPP_PHONE_NUMBER_ID
        self.business_id = WHATSAPP_BUSINESS_ID
        self.api_version = WHATSAPP_API_VERSION
        self.base_url = f"https://graph.facebook.com/{self.api_version}/{self.phone_number_id}/messages"

    def format_phone_number(self, phone: str) -> str:
        """
        Format phone number for WhatsApp (must include country code)
        Tanzania country code: +255
        Converts: 0781588379 -> 255781588379
        """
        # Remove any spaces, dashes, or plus signs
        phone = phone.replace(" ", "").replace("-", "").replace("+", "")

        # If phone starts with 0, replace with Tanzania country code (255)
        if phone.startswith("0"):
            phone = "255" + phone[1:]

        # If doesn't start with country code, add Tanzania code
        elif not phone.startswith("255"):
            phone = "255" + phone

        return phone

    def send_credentials_message(
        self, phone: str, username: str, password: str, plan_type: str, buyer_name: str
    ):
        """
        Send internet access credentials via WhatsApp

        Args:
            phone: Customer phone number (e.g., "0781588379")
            username: Generated username
            password: Generated password
            plan_type: "daily_1000" or "monthly_1000"
            buyer_name: Customer name

        Returns:
            dict: Response from WhatsApp API or error details
        """
        # Format phone number
        formatted_phone = self.format_phone_number(phone)

        # Determine plan name
        if plan_type == "daily_1000":
            plan_name_en = "Daily Plan (24 hours)"
            plan_name_sw = "Mpango wa Siku (Masaa 24)"
        elif plan_type == "monthly_1000":
            plan_name_en = "Monthly Plan (30 days)"
            plan_name_sw = "Mpango wa Mwezi (Siku 30)"
        else:
            plan_name_en = plan_type
            plan_name_sw = plan_type

        # Create bilingual message
        message = f"""*uCHiPaNi Networks* 🌐

Habari {buyer_name}! / Hello {buyer_name}!

Malipo yako yamefanikiwa! Hizi ndizo hati zako za kuingia mtandaoni:
Your payment was successful! Here are your internet access credentials:

*Jina la Mtumiaji / Username:*
`{username}`

*Neno la Siri / Password:*
`{password}`

*Mpango / Plan:*
{plan_name_sw} / {plan_name_en}

*Jinsi ya Kuingia / How to Login:*
1. Fungua mtandao wa WiFi / Connect to WiFi
2. Fungua kivinjari / Open your browser
3. Ingiza jina na neno la siri / Enter username and password

Asante kwa kuchagua huduma zetu! 🎉
Thank you for choosing our service! 🎉

_Hati hizi ni za siri. Usizishirikishe na mtu mwingine._
_These credentials are confidential. Do not share with others._"""

        # Prepare request payload
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": formatted_phone,
            "type": "text",
            "text": {"preview_url": False, "body": message},
        }

        # Request headers
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

        try:
            # Send request to WhatsApp API
            response = requests.post(self.base_url, json=payload, headers=headers, timeout=10)

            # Check response
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "message_id": result.get("messages", [{}])[0].get("id"),
                    "phone": formatted_phone,
                }
            else:
                error_data = response.json()
                return {
                    "success": False,
                    "error": error_data.get("error", {}).get("message", "Unknown error"),
                    "status_code": response.status_code,
                    "phone": formatted_phone,
                }

        except requests.exceptions.Timeout:
            return {
                "success": False,
                "error": "Request timeout - WhatsApp API did not respond in time",
                "phone": formatted_phone,
            }
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": f"Network error: {str(e)}",
                "phone": formatted_phone,
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "phone": formatted_phone,
            }

    def send_payment_reminder(self, phone: str, buyer_name: str, payment_link: str):
        """
        Send payment reminder with link

        Args:
            phone: Customer phone number
            buyer_name: Customer name
            payment_link: ZenoPay payment link

        Returns:
            dict: Response from WhatsApp API
        """
        formatted_phone = self.format_phone_number(phone)

        message = f"""*uCHiPaNi Networks* 🌐

Habari {buyer_name}!

Endelea kulipa malipo yako kwa kubofya kiungo hiki:
Complete your payment by clicking this link:

{payment_link}

Asante! / Thank you!"""

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": formatted_phone,
            "type": "text",
            "text": {"preview_url": True, "body": message},
        }

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(self.base_url, json=payload, headers=headers, timeout=10)

            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "message_id": result.get("messages", [{}])[0].get("id"),
                }
            else:
                return {"success": False, "error": response.json()}

        except Exception as e:
            return {"success": False, "error": str(e)}


# Global instance
whatsapp_service = WhatsAppService()
