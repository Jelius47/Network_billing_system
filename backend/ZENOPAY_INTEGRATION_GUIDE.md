# ZenoPay Integration Guide

## Overview

This system allows customers to pay for internet access using ZenoPay and automatically receive login credentials. The entire process is self-service.

## System Flow

1. Customer visits hotspot login page
2. Customer clicks "Buy Internet Access"
3. Customer enters phone number, email, and selects plan
4. System generates ZenoPay payment link
5. Customer pays via ZenoPay
6. System automatically:
   - Creates user in MikroTik with uptime limits
   - Generates and saves credentials
   - Displays credentials to customer
7. Customer uses credentials to access internet
8. Admin can view all auto-generated users in dashboard

## Configuration

### 1. Update .env File on Server

```bash
# Add these to your server's .env file
ZENOPAY_API_KEY=your_actual_zenopay_api_key
ZENOPAY_PIN=your_zenopay_pin
ZENOPAY_WEBHOOK_URL=http://YOUR_SERVER_IP/api/payments/webhook

# Set your prices (in TZS)
DAILY_PLAN_PRICE=1000
MONTHLY_PLAN_PRICE=30000
```

### 2. Deploy Updated Code to Server

```bash
# From your local machine, copy files to server
scp /Users/jelius/Documents/personal_pro/networking_mikrotik/backend/payment_service.py root@164.90.233.185:/root/Network_billing_system/backend/
scp /Users/jelius/Documents/personal_pro/networking_mikrotik/backend/main.py root@164.90.233.185:/root/Network_billing_system/backend/
scp /Users/jelius/Documents/personal_pro/networking_mikrotik/backend/database.py root@164.90.233.185:/root/Network_billing_system/backend/
scp /Users/jelius/Documents/personal_pro/networking_mikrotik/backend/mikrotik_api.py root@164.90.233.185:/root/Network_billing_system/backend/
scp /Users/jelius/Documents/personal_pro/networking_mikrotik/backend/.env root@164.90.233.185:/root/Network_billing_system/backend/

# SSH to server and restart backend
ssh root@164.90.233.185 "systemctl restart mikrotik-backend && systemctl status mikrotik-backend"
```

## API Endpoints

### 1. Create Payment Checkout

**Endpoint:** `POST /payments/create-checkout`

**Request:**
```json
{
  "phone": "0781588379",
  "email": "customer@example.com",
  "plan_type": "daily_1000",
  "redirect_url": "https://yourwebsite.com/payment-success"
}
```

**Response:**
```json
{
  "payment_link": "https://zenopay.co.tz/checkout/...",
  "tx_ref": "unique_transaction_reference",
  "amount": 1000,
  "plan_type": "daily_1000"
}
```

### 2. Check Payment Status

**Endpoint:** `GET /payments/check/{tx_ref}`

**Response (pending):**
```json
{
  "status": "PENDING",
  "message": "Payment not yet completed"
}
```

**Response (completed):**
```json
{
  "status": "COMPLETED",
  "username": "user_20231208143022_5432",
  "password": "Xy9K2mPq",
  "plan_type": "daily_1000",
  "expiry": "2023-12-09T14:30:22Z"
}
```

### 3. List All Payment Transactions (Admin)

**Endpoint:** `GET /payments/transactions`

**Response:**
```json
[
  {
    "id": 1,
    "tx_ref": "abc123",
    "phone": "0781588379",
    "email": "customer@example.com",
    "plan_type": "daily_1000",
    "amount": 1000,
    "status": "COMPLETED",
    "user_id": 5,
    "created_at": "2023-12-08T14:30:22Z",
    "completed_at": "2023-12-08T14:32:15Z"
  }
]
```

### 4. Webhook (ZenoPay calls this)

**Endpoint:** `POST /payments/webhook`

This is automatically called by ZenoPay when payment status changes.

## Frontend Integration

### Create Payment Page

Create a new page in your React frontend:

**File: `frontend/src/components/BuyInternet.js`**

```javascript
import React, { useState } from 'react';
import API_BASE_URL from '../config';

function BuyInternet() {
  const [formData, setFormData] = useState({
    phone: '',
    email: '',
    plan_type: 'daily_1000'
  });
  const [loading, setLoading] = useState(false);
  const [paymentLink, setPaymentLink] = useState('');
  const [txRef, setTxRef] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/payments/create-checkout`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...formData,
          redirect_url: window.location.origin + '/payment-success'
        })
      });

      const data = await response.json();
      setPaymentLink(data.payment_link);
      setTxRef(data.tx_ref);

      // Redirect to payment page
      window.location.href = data.payment_link;
    } catch (error) {
      alert('Failed to create payment: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="buy-internet">
      <h2>Buy Internet Access</h2>
      <form onSubmit={handleSubmit}>
        <div>
          <label>Phone Number:</label>
          <input
            type="tel"
            value={formData.phone}
            onChange={(e) => setFormData({...formData, phone: e.target.value})}
            placeholder="0781588379"
            required
          />
        </div>

        <div>
          <label>Email:</label>
          <input
            type="email"
            value={formData.email}
            onChange={(e) => setFormData({...formData, email: e.target.value})}
            placeholder="your@email.com"
            required
          />
        </div>

        <div>
          <label>Plan:</label>
          <select
            value={formData.plan_type}
            onChange={(e) => setFormData({...formData, plan_type: e.target.value})}
          >
            <option value="daily_1000">Daily - 1,000 TZS (24 hours)</option>
            <option value="monthly_1000">Monthly - 30,000 TZS (30 days)</option>
          </select>
        </div>

        <button type="submit" disabled={loading}>
          {loading ? 'Creating payment...' : 'Pay Now'}
        </button>
      </form>
    </div>
  );
}

export default BuyInternet;
```

### Payment Success Page

**File: `frontend/src/components/PaymentSuccess.js`**

```javascript
import React, { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import API_BASE_URL from '../config';

function PaymentSuccess() {
  const [searchParams] = useSearchParams();
  const [credentials, setCredentials] = useState(null);
  const [loading, setLoading] = useState(true);
  const txRef = searchParams.get('tx_ref');

  useEffect(() => {
    if (!txRef) return;

    // Poll for payment completion
    const checkPayment = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/payments/check/${txRef}`);
        const data = await response.json();

        if (data.status === 'COMPLETED') {
          setCredentials(data);
          setLoading(false);
        } else {
          // Keep polling every 3 seconds
          setTimeout(checkPayment, 3000);
        }
      } catch (error) {
        console.error('Error checking payment:', error);
        setTimeout(checkPayment, 3000);
      }
    };

    checkPayment();
  }, [txRef]);

  if (loading) {
    return (
      <div>
        <h2>Processing Payment...</h2>
        <p>Please wait while we confirm your payment and create your account.</p>
      </div>
    );
  }

  return (
    <div className="payment-success">
      <h2>Payment Successful!</h2>
      <div className="credentials-box">
        <h3>Your Internet Access Credentials</h3>
        <p><strong>Username:</strong> {credentials.username}</p>
        <p><strong>Password:</strong> {credentials.password}</p>
        <p><strong>Plan:</strong> {credentials.plan_type}</p>
        <p><strong>Valid Until:</strong> {new Date(credentials.expiry).toLocaleString()}</p>
      </div>
      <div className="instructions">
        <h4>How to Connect:</h4>
        <ol>
          <li>Connect to the WiFi network</li>
          <li>Open your browser</li>
          <li>Enter these credentials when prompted</li>
          <li>Start browsing!</li>
        </ol>
      </div>
      <button onClick={() => window.print()}>Print Credentials</button>
    </div>
  );
}

export default PaymentSuccess;
```

### Add Payment Transactions to Admin Dashboard

Update your admin dashboard to show payment transactions:

```javascript
// In your admin dashboard component
const [transactions, setTransactions] = useState([]);

useEffect(() => {
  fetch(`${API_BASE_URL}/payments/transactions`)
    .then(res => res.json())
    .then(data => setTransactions(data));
}, []);

return (
  <div>
    <h3>Payment Transactions</h3>
    <table>
      <thead>
        <tr>
          <th>TX Ref</th>
          <th>Phone</th>
          <th>Email</th>
          <th>Plan</th>
          <th>Amount</th>
          <th>Status</th>
          <th>Date</th>
        </tr>
      </thead>
      <tbody>
        {transactions.map(tx => (
          <tr key={tx.id}>
            <td>{tx.tx_ref}</td>
            <td>{tx.phone}</td>
            <td>{tx.email}</td>
            <td>{tx.plan_type}</td>
            <td>{tx.amount} TZS</td>
            <td>{tx.status}</td>
            <td>{new Date(tx.created_at).toLocaleString()}</td>
          </tr>
        ))}
      </tbody>
    </table>
  </div>
);
```

## ZenoPay Dashboard Configuration

1. Log in to your ZenoPay account at https://zenopay.co.tz
2. Go to Settings > Webhooks
3. Add webhook URL: `http://YOUR_SERVER_IP/api/payments/webhook`
4. Enable events: `payment.completed`, `payment.failed`
5. Save and note your API key
6. Update your .env file with the API key

## Testing

### Test Payment Flow

```bash
# 1. Create a checkout
curl -X POST http://YOUR_SERVER_IP/api/payments/create-checkout \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "0781588379",
    "email": "test@example.com",
    "plan_type": "daily_1000"
  }'

# Response will include payment_link and tx_ref

# 2. Visit the payment_link and complete payment (use ZenoPay test mode)

# 3. Check payment status
curl http://YOUR_SERVER_IP/api/payments/check/TX_REF_FROM_STEP_1
```

## Features

### Auto-Generated Users

- Username format: `user_YYYYMMDDHHMMSS_XXXX` (e.g., `user_20231208143022_5432`)
- Password: 8 random characters (alphanumeric)
- Credentials are visible in admin dashboard
- Users marked with `auto_generated=true` in database

### Uptime Limits

- Daily plan: 24 hours of actual usage (not calendar days)
- Monthly plan: 30 days of actual usage (not calendar days)
- Countdown only happens when user is connected

### Admin Visibility

All auto-generated users appear in the admin dashboard with:
- Username and password
- Customer phone and email
- Transaction reference
- Payment amount
- Creation date
- Expiry date
- Active status

## Troubleshooting

### Webhook Not Being Called

1. Check ZenoPay webhook configuration
2. Ensure webhook URL is publicly accessible
3. Check server logs: `journalctl -u mikrotik-backend -f`

### Payment Completed But No User Created

1. Check backend logs for errors
2. Verify MikroTik connection is working
3. Check database for transaction status

### User Created But Can't Access Internet

1. Verify user exists in MikroTik: `/ip hotspot user print`
2. Check user is active in database
3. Verify hotspot profiles (daily_1000, monthly_1000) exist

## Next Steps

1. Set up email/SMS notifications to send credentials to customers
2. Add payment receipt generation
3. Implement refund functionality
4. Add payment analytics to admin dashboard
5. Set up automatic expiry notifications

## Support

For issues with:
- ZenoPay integration: Contact ZenoPay support or check SDK docs
- Backend errors: Check `journalctl -u mikrotik-backend`
- Frontend issues: Check browser console

