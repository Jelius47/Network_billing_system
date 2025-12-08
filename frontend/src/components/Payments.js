import React, { useState, useEffect } from 'react';
import axios from 'axios';
import API_BASE_URL from '../config';

function Payments() {
  const [users, setUsers] = useState([]);
  const [payments, setPayments] = useState([]);
  const [formData, setFormData] = useState({
    user_id: '',
    amount: ''
  });
  const [message, setMessage] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchUsers();
    fetchPayments();
  }, []);

  const fetchUsers = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/users`);
      setUsers(response.data);
    } catch (error) {
      console.error('Error fetching users:', error);
    }
  };

  const fetchPayments = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/payments`);
      setPayments(response.data);
    } catch (error) {
      console.error('Error fetching payments:', error);
    }
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage(null);

    try {
      await axios.post(`${API_BASE_URL}/payments`, {
        user_id: parseInt(formData.user_id),
        amount: parseFloat(formData.amount)
      });

      setMessage({ type: 'success', text: 'Payment recorded successfully!' });

      // Reset form
      setFormData({
        user_id: '',
        amount: ''
      });

      // Refresh payments list
      fetchPayments();

      setTimeout(() => setMessage(null), 3000);
    } catch (error) {
      const errorMsg = error.response?.data?.detail || 'Failed to record payment';
      setMessage({ type: 'error', text: errorMsg });
      setTimeout(() => setMessage(null), 3000);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  const getUserName = (userId) => {
    const user = users.find(u => u.id === userId);
    return user ? user.username : `User #${userId}`;
  };

  return (
    <div>
      <div className="card">
        <h2>Record Payment</h2>

        {message && (
          <div className={`message message-${message.type}`}>
            {message.text}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="user_id">Select User</label>
            <select
              id="user_id"
              name="user_id"
              value={formData.user_id}
              onChange={handleChange}
              required
            >
              <option value="">-- Select User --</option>
              {users.map((user) => (
                <option key={user.id} value={user.id}>
                  {user.username} ({user.plan_type})
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="amount">Amount</label>
            <input
              type="number"
              id="amount"
              name="amount"
              value={formData.amount}
              onChange={handleChange}
              required
              step="0.01"
              min="0"
              placeholder="Enter amount"
            />
          </div>

          <button type="submit" className="btn btn-success" disabled={loading}>
            {loading ? 'Recording...' : 'Record Payment'}
          </button>
        </form>
      </div>

      <div className="card">
        <h2>Payment History</h2>

        <table>
          <thead>
            <tr>
              <th>Date</th>
              <th>User</th>
              <th>Amount</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {payments.map((payment) => (
              <tr key={payment.id}>
                <td>{formatDate(payment.date)}</td>
                <td>{getUserName(payment.user_id)}</td>
                <td>${payment.amount.toFixed(2)}</td>
                <td>
                  <span className="status-active">
                    {payment.verified ? 'Verified' : 'Pending'}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {payments.length === 0 && (
          <p style={{ textAlign: 'center', marginTop: '2rem', color: '#666' }}>
            No payments recorded yet.
          </p>
        )}
      </div>
    </div>
  );
}

export default Payments;
