import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import API_BASE_URL from '../config';

function AddUser() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    username: '',
    password: '',
    plan_type: 'daily_1000'
  });
  const [message, setMessage] = useState(null);
  const [loading, setLoading] = useState(false);

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
      await axios.post(`${API_BASE_URL}/users`, formData);
      setMessage({ type: 'success', text: 'User created successfully!' });

      // Reset form
      setFormData({
        username: '',
        password: '',
        plan_type: 'daily_1000'
      });

      // Redirect to user list after 2 seconds
      setTimeout(() => {
        navigate('/users');
      }, 2000);
    } catch (error) {
      const errorMsg = error.response?.data?.detail || 'Failed to create user';
      setMessage({ type: 'error', text: errorMsg });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card">
      <h2>Add New User</h2>

      {message && (
        <div className={`message message-${message.type}`}>
          {message.text}
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="username">Username</label>
          <input
            type="text"
            id="username"
            name="username"
            value={formData.username}
            onChange={handleChange}
            required
            placeholder="Enter username"
          />
        </div>

        <div className="form-group">
          <label htmlFor="password">Password</label>
          <input
            type="password"
            id="password"
            name="password"
            value={formData.password}
            onChange={handleChange}
            required
            placeholder="Enter password"
          />
        </div>

        <div className="form-group">
          <label htmlFor="plan_type">Plan Type</label>
          <select
            id="plan_type"
            name="plan_type"
            value={formData.plan_type}
            onChange={handleChange}
            required
          >
            <option value="daily_1000">Daily - 1000 (24 hours)</option>
            <option value="monthly_1000">Monthly - 1000 (30 days)</option>
          </select>
        </div>

        <button type="submit" className="btn btn-primary" disabled={loading}>
          {loading ? 'Creating...' : 'Create User'}
        </button>
      </form>
    </div>
  );
}

export default AddUser;
