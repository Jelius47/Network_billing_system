import React, { useState, useEffect } from 'react';
import axios from 'axios';
import API_BASE_URL from '../config';

function UserList() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState(null);

  useEffect(() => {
    fetchUsers();
    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchUsers, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchUsers = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/users`);
      setUsers(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching users:', error);
      setLoading(false);
    }
  };

  const toggleUser = async (userId) => {
    try {
      await axios.post(`${API_BASE_URL}/users/${userId}/toggle`);
      setMessage({ type: 'success', text: 'User status toggled successfully' });
      fetchUsers();
      setTimeout(() => setMessage(null), 3000);
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to toggle user status' });
      setTimeout(() => setMessage(null), 3000);
    }
  };

  const extendUser = async (userId, days) => {
    try {
      await axios.post(`${API_BASE_URL}/users/${userId}/extend`, { days });
      setMessage({ type: 'success', text: `User extended by ${days} days` });
      fetchUsers();
      setTimeout(() => setMessage(null), 3000);
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to extend user' });
      setTimeout(() => setMessage(null), 3000);
    }
  };

  const deleteUser = async (userId, username) => {
    if (!window.confirm(`Are you sure you want to delete user "${username}"? This will remove them from both MikroTik and the database. This action cannot be undone.`)) {
      return;
    }

    try {
      await axios.delete(`${API_BASE_URL}/users/${userId}`);
      setMessage({ type: 'success', text: `User "${username}" deleted successfully` });
      fetchUsers();
      setTimeout(() => setMessage(null), 3000);
    } catch (error) {
      setMessage({ type: 'error', text: error.response?.data?.detail || 'Failed to delete user' });
      setTimeout(() => setMessage(null), 5000);
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  const isExpired = (expiryString) => {
    return new Date(expiryString) < new Date();
  };

  if (loading) {
    return <div className="loading">Loading...</div>;
  }

  return (
    <div className="card">
      <h2>User Management</h2>

      {message && (
        <div className={`message message-${message.type}`}>
          {message.text}
        </div>
      )}

      <table>
        <thead>
          <tr>
            <th>Username</th>
            <th>Plan</th>
            <th>Expiry</th>
            <th>Status</th>
            <th>Created</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {users.map((user) => (
            <tr key={user.id}>
              <td>{user.username}</td>
              <td>{user.plan_type}</td>
              <td>
                <span className={isExpired(user.expiry) ? 'status-expired' : ''}>
                  {formatDate(user.expiry)}
                </span>
              </td>
              <td>
                <span className={user.is_active ? 'status-active' : 'status-expired'}>
                  {user.is_active ? 'Active' : 'Inactive'}
                </span>
              </td>
              <td>{formatDate(user.created_at)}</td>
              <td>
                <div className="actions">
                  <button
                    className={`btn btn-small ${user.is_active ? 'btn-danger' : 'btn-success'}`}
                    onClick={() => toggleUser(user.id)}
                  >
                    {user.is_active ? 'Disable' : 'Enable'}
                  </button>
                  <button
                    className="btn btn-small btn-primary"
                    onClick={() => extendUser(user.id, user.plan_type === 'daily_1000' ? 1 : 30)}
                  >
                    Extend
                  </button>
                  <button
                    className="btn btn-small btn-delete"
                    onClick={() => deleteUser(user.id, user.username)}
                  >
                    Delete
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {users.length === 0 && (
        <p style={{ textAlign: 'center', marginTop: '2rem', color: '#666' }}>
          No users found. Add your first user to get started.
        </p>
      )}
    </div>
  );
}

export default UserList;
