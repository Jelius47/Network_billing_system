# WhatsApp Business API Setup Guide

This guide explains how to set up WhatsApp Business API to automatically send internet credentials to customers after successful payment.

## Prerequisites

- A Facebook Business Account
- A verified WhatsApp Business Account
- A phone number registered with WhatsApp Business API

## Step 1: Get WhatsApp Business API Access

### Option A: Using Meta (Facebook) Directly

1. Go to [Meta for Developers](https://developers.facebook.com/)
2. Create or select your app
3. Add "WhatsApp" product to your app
4. Complete the setup wizard

### Option B: Using Cloud API (Recommended)

1. Go to [Meta Business Suite](https://business.facebook.com/)
2. Navigate to WhatsApp Manager
3. Set up WhatsApp Business API with Cloud API
4. This is free for the first 1,000 conversations per month

## Step 2: Get Required Credentials

You need 4 pieces of information from Meta:

### 1. Access Token (`WHATSAPP_ACCESS_TOKEN`)
- Go to your Meta App Dashboard
- Navigate to **WhatsApp > Getting Started**
- Copy the **Temporary Access Token** (valid for 24 hours)
- For production, create a **System User Access Token** (permanent):
  - Go to Business Settings > System Users
  - Create a system user
  - Generate a token with `whatsapp_business_messaging` permission

### 2. Phone Number ID (`WHATSAPP_PHONE_NUMBER_ID`)
- In WhatsApp Manager, go to **API Setup**
- Under "Phone Number", copy the **Phone Number ID** (not the actual phone number)
- Example: `123456789012345`

### 3. Business Account ID (`WHATSAPP_BUSINESS_ID`)
- Go to Business Settings
- Under "Business Info", find your **WhatsApp Business Account ID**
- Example: `987654321098765`

### 4. API Version (`WHATSAPP_API_VERSION`)
- Default is `v21.0` (current latest version)
- Check [WhatsApp API Changelog](https://developers.facebook.com/docs/whatsapp/changelog) for updates

## Step 3: Configure Environment Variables

Update your `.env` file with the credentials:

```env
# WhatsApp Business API Configuration
WHATSAPP_ACCESS_TOKEN=your_actual_access_token_here
WHATSAPP_PHONE_NUMBER_ID=123456789012345
WHATSAPP_BUSINESS_ID=987654321098765
WHATSAPP_API_VERSION=v21.0
```

## Step 4: Test the Integration

### Manual Test

You can test the WhatsApp service directly:

```python
from whatsapp_service import whatsapp_service

result = whatsapp_service.send_credentials_message(
    phone="0781588379",  # Your test phone number
    username="test_user_123",
    password="testpass123",
    plan_type="daily_1000",
    buyer_name="Test User"
)

print(result)
```

### Expected Response

Success:
```json
{
    "success": true,
    "message_id": "wamid.HBgLMjU1Nzgx...",
    "phone": "255781588379"
}
```

Failure:
```json
{
    "success": false,
    "error": "Invalid access token",
    "status_code": 401,
    "phone": "255781588379"
}
```

## Step 5: Verify Phone Number Format

The service automatically converts Tanzanian phone numbers:
- Input: `0781588379`
- Converted: `255781588379`

If your customers use different country codes, update the `format_phone_number()` method in `whatsapp_service.py`.

## Step 6: Message Template (Optional)

For production use at scale, you may need to create approved message templates:

1. Go to WhatsApp Manager > Message Templates
2. Create a template for "Authentication Credentials"
3. Submit for approval
4. Update `whatsapp_service.py` to use the template

Current implementation uses **freeform messages** which work for:
- First 1,000 conversations per month (free tier)
- 24-hour session after customer initiates conversation

## Troubleshooting

### Error: "Invalid access token"
- Generate a new access token
- Ensure system user token has `whatsapp_business_messaging` permission

### Error: "Phone number not registered"
- Customer's WhatsApp must be active
- Phone number must be correct format

### Error: "Template not found"
- If using templates, ensure template is approved
- For freeform messages, ensure within 24-hour session window

### Message not received
- Check phone number format
- Verify customer has WhatsApp installed
- Check WhatsApp Business API webhook logs in Meta Dashboard

## Cost Information

**Meta Cloud API Pricing (as of 2024):**
- First 1,000 conversations/month: FREE
- Authentication messages: $0.005 - $0.009 per message (Tanzania)
- Marketing messages: Higher rates

**Conversation Window:**
- 24 hours after last customer message
- Freeform messages allowed within window
- Template messages required outside window

## Production Recommendations

1. **Use System User Access Token** (not temporary token)
2. **Set up webhook** to receive message status updates
3. **Implement retry logic** for failed messages
4. **Monitor API usage** in Meta Business Suite
5. **Create message templates** for better deliverability
6. **Add rate limiting** to avoid API throttling

## Security Best Practices

1. Never commit `.env` file to version control
2. Rotate access tokens periodically
3. Use system user with minimal permissions
4. Log all WhatsApp API calls for auditing
5. Implement proper error handling

## Support & Resources

- [WhatsApp Business API Documentation](https://developers.facebook.com/docs/whatsapp/cloud-api)
- [WhatsApp Business Platform](https://business.whatsapp.com/)
- [Meta for Developers Community](https://developers.facebook.com/community/)

## Current Implementation Flow

1. Customer completes payment via ZenoPay
2. ZenoPay sends webhook to `/api/payments/webhook`
3. System generates username & password
4. System creates user in MikroTik and database
5. **System sends credentials via WhatsApp automatically**
6. Customer receives message within seconds
7. Credentials also stored in database for retrieval

## Backup: Credentials Retrieval

If WhatsApp fails, customers can still retrieve credentials:
- Credentials are displayed on payment success page
- Admin can view all credentials in admin panel
- Implement `/api/payments/resend-credentials` endpoint for manual resend

---

**Need Help?** Contact Meta Business Support or check the implementation in `whatsapp_service.py`
