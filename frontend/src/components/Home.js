import React, { useState, useEffect } from 'react';
import axios from 'axios';
import API_BASE_URL from '../config';

function Home() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats();
    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchStats, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchStats = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/stats`);
      setStats(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching stats:', error);
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="loading">Loading...</div>;
  }

  return (
    <div>
      <div className="card">
        <h2>Dashboard Overview</h2>
        <p>Welcome to the MikroTik Billing System</p>
      </div>

      {stats && (
        <div className="stats-grid">
          <div className="stat-card">
            <h3>Total Users</h3>
            <div className="number">{stats.total_users}</div>
          </div>

          <div className="stat-card green">
            <h3>Active Users</h3>
            <div className="number">{stats.active_users}</div>
          </div>

          <div className="stat-card orange">
            <h3>Expired Users</h3>
            <div className="number">{stats.expired_users}</div>
          </div>

          <div className="stat-card blue">
            <h3>Total Payments</h3>
            <div className="number">{stats.total_payments}</div>
          </div>
        </div>
      )}
    </div>
  );
}

export default Home;
