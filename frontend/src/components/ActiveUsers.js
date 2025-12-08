import React, { useState, useEffect } from 'react';
import axios from 'axios';
import API_BASE_URL from '../config';
import './ActiveUsers.css';

function ActiveUsers() {
    const [activeUsers, setActiveUsers] = useState([]);
    const [count, setCount] = useState(0);
    const [loading, setLoading] = useState(true);
    const [syncing, setSyncing] = useState(false);
    const [message, setMessage] = useState(null);
    const [lastUpdate, setLastUpdate] = useState(null);

    const fetchActiveUsers = async () => {
        try {
            const response = await axios.get(`${API_BASE_URL}/active-connections`);
            setActiveUsers(response.data.users || []);
            setCount(response.data.count || 0);
            setLastUpdate(new Date().toLocaleTimeString());
            setLoading(false);
        } catch (error) {
            console.error('Error fetching active users:', error);
            setLoading(false);
        }
    };

    const syncUsers = async () => {
        setSyncing(true);
        setMessage(null);
        try {
            const response = await axios.post(`${API_BASE_URL}/sync-users`);
            if (response.data.success) {
                setMessage({
                    type: 'success',
                    text: `${response.data.message} (MikroTik: ${response.data.mikrotik_total}, Database: ${response.data.database_total})`
                });
            } else {
                setMessage({ type: 'error', text: response.data.message });
            }
        } catch (error) {
            setMessage({ type: 'error', text: 'Failed to sync users' });
        }
        setSyncing(false);
        // Refresh active users after sync
        setTimeout(fetchActiveUsers, 1000);
    };

    useEffect(() => {
        fetchActiveUsers();
        // Auto-refresh every 15 seconds
        const interval = setInterval(fetchActiveUsers, 15000);
        return () => clearInterval(interval);
    }, []);

    const formatSessionTime = (uptimeStr) => {
        if (!uptimeStr) return 'N/A';
        // Parse MikroTik uptime format (e.g., "1h2m3s" or "2m30s")
        return uptimeStr;
    };

    return (
        <div className="active-users-container">
            <div className="active-users-header">
                <div className="header-left">
                    <h2>Active Connections</h2>
                    <span className="user-count">{count} user{count !== 1 ? 's' : ''} online</span>
                    {lastUpdate && <span className="last-update">Last updated: {lastUpdate}</span>}
                </div>
                <div className="header-right">
                    <button
                        onClick={fetchActiveUsers}
                        className="refresh-btn"
                        disabled={loading}
                    >
                        {loading ? 'Refreshing...' : 'Refresh'}
                    </button>
                    <button
                        onClick={syncUsers}
                        className="sync-btn"
                        disabled={syncing}
                    >
                        {syncing ? 'Syncing...' : 'Sync Database'}
                    </button>
                </div>
            </div>

            {message && (
                <div className={`message ${message.type}`}>
                    {message.text}
                </div>
            )}

            {loading ? (
                <div className="loading">Loading active users...</div>
            ) : activeUsers.length === 0 ? (
                <div className="no-users">
                    <p>No active users connected</p>
                    <small>Users must authenticate through the hotspot login page</small>
                </div>
            ) : (
                <div className="active-users-table">
                    <table>
                        <thead>
                            <tr>
                                <th>Username</th>
                                <th>IP Address</th>
                                <th>MAC Address</th>
                                <th>Session Time</th>
                                <th>Login Time</th>
                            </tr>
                        </thead>
                        <tbody>
                            {activeUsers.map((user, index) => (
                                <tr key={index}>
                                    <td className="username">{user.user || 'N/A'}</td>
                                    <td>{user.address || 'N/A'}</td>
                                    <td className="mac-address">{user['mac-address'] || 'N/A'}</td>
                                    <td>{formatSessionTime(user.uptime)}</td>
                                    <td>{user['login-by'] || 'hotspot'}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}

            <div className="info-box">
                <h4>About Active Connections:</h4>
                <ul>
                    <li><strong>Active:</strong> Users currently authenticated and online</li>
                    <li><strong>Auto-refresh:</strong> Updates every 15 seconds</li>
                    <li><strong>Sync Database:</strong> Removes users from database that no longer exist in MikroTik</li>
                </ul>
            </div>
        </div>
    );
}

export default ActiveUsers;
