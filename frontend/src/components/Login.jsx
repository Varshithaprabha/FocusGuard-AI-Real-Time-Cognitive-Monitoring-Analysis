import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

const Login = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await axios.post('http://localhost:8000/api/login', {
        username,
        password
      });

      if (response.data.success) {
        // Store in localStorage
        localStorage.setItem('user', JSON.stringify({
          user_id: response.data.user_id,
          username: response.data.username,
          role: response.data.role
        }));
        navigate('/dashboard');
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to login. Ensure FastAPI server is running.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-box glass-panel animate-fade-in">
        <h1>AI Study Planner</h1>
        <p>Login to your interactive dashboard</p>
        
        <form onSubmit={handleLogin}>
          <div className="input-group">
            <label>Username</label>
            <input 
              type="text" 
              placeholder="Enter username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
          </div>
          
          <div className="input-group">
            <label>Password</label>
            <input 
              type="password" 
              placeholder="Enter password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          {error && <span className="error-text">{error}</span>}
          
          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? 'Authenticating...' : 'Log In'}
          </button>
        </form>

        <div style={{marginTop: '2rem', fontSize: '0.8rem', color: 'var(--text-muted)'}}>
          <p>Don't have an account? Just enter a new username and password to register automatically!</p>
          <p>To access the global dashboard, use Dev: admin / admin123</p>
        </div>
      </div>
    </div>
  );
};

export default Login;
