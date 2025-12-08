import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import './App.css';
import Home from './components/Home';
import UserList from './components/UserList';
import AddUser from './components/AddUser';
import Payments from './components/Payments';

function App() {
  return (
    <Router>
      <div className="App">
        <nav className="navbar">
          <h1>MikroTik Billing System</h1>
          <div className="nav-links">
            <Link to="/">Home</Link>
            <Link to="/users">Users</Link>
            <Link to="/add-user">Add User</Link>
            <Link to="/payments">Payments</Link>
          </div>
        </nav>

        <div className="container">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/users" element={<UserList />} />
            <Route path="/add-user" element={<AddUser />} />
            <Route path="/payments" element={<Payments />} />
          </Routes>
        </div>
      </div>
    </Router>
  );
}

export default App;
