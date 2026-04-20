import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  BarElement
} from 'chart.js';
import { Line, Pie, Bar } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  BarElement
);

const Dashboard = () => {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [summaryData, setSummaryData] = useState([]);
  const [logsData, setLogsData] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [toastMessage, setToastMessage] = useState("");

  useEffect(() => {
    const storedUser = localStorage.getItem('user');
    if (!storedUser) {
      navigate('/login');
      return;
    }
    const parsedUser = JSON.parse(storedUser);
    setUser(parsedUser);
    fetchData(parsedUser);

    // Real-time updates via WebSockets
    const wsUrl = import.meta.env.VITE_WEBSOCKET_URL 
      ? `${import.meta.env.VITE_WEBSOCKET_URL}${parsedUser.user_id}` 
      : `ws://localhost:8000/ws/dashboard/${parsedUser.user_id}`;
      
    const ws = new WebSocket(wsUrl);
    ws.onmessage = (event) => {
      if (event.data === "UPDATE_AVAILABLE") {
        fetchData(parsedUser).then(newLogs => {
          if (newLogs && newLogs.length > 0) {
            let slouchSlices = newLogs.slice(-6); // Last 30 seconds
            let slouchCount = slouchSlices.filter(l => l.state === "Bad Posture").length;
            if (slouchCount >= 6) {
              setToastMessage("Hey, sit up! Your back will thank you.");
              setTimeout(() => setToastMessage(""), 5000);
            }
          }
        });
      }
    };
    ws.onerror = (error) => console.error("WebSocket Error:", error);

    return () => ws.close();
  }, [navigate]);

  const fetchData = async (userData) => {
    try {
      const summaryRes = await axios.get(`http://localhost:8000/api/summary/${userData.user_id}?role=${userData.role}`);
      setSummaryData(summaryRes.data);
      
      const logsRes = await axios.get(`http://localhost:8000/api/logs/${userData.user_id}`);
      setLogsData(logsRes.data);
      
      try {
        const anRes = await axios.get(`http://localhost:8000/api/analytics/${userData.user_id}`);
        setAnalytics(anRes.data);
      } catch (e) {
        setAnalytics(null);
      }
      
      return logsRes.data;
    } catch (error) {
      console.error("Error fetching data:", error);
      return null;
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('user');
    navigate('/login');
  };

  if (loading || !user) {
    return <div className="login-container">Loading Dashboard...</div>;
  }

  // Calculate Metrics
  const totalSessions = summaryData.length;
  const avgScore = totalSessions ? (summaryData.reduce((acc, curr) => acc + curr.final_score, 0) / totalSessions).toFixed(1) : 0;
  const totalFocusTime = summaryData.reduce((acc, curr) => acc + curr.focus_time, 0).toFixed(1);
  const totalDistractionTime = summaryData.reduce((acc, curr) => acc + curr.distraction_time, 0).toFixed(1);
  const totalAbsenceTime = summaryData.reduce((acc, curr) => acc + curr.absence_time, 0).toFixed(1);

  // Line Chart Data
  const lineData = {
    labels: summaryData.map((s, i) => user.role === 'developer' ? `${s.username} (Ses: ${s.session_id})` : `Session ${i+1}`),
    datasets: [
      {
        label: 'Focus Score',
        data: summaryData.map(s => s.final_score),
        borderColor: '#6366f1',
        backgroundColor: 'rgba(99, 102, 241, 0.5)',
        tension: 0.3,
        fill: true,
      }
    ]
  };

  // Pie Chart Data
  const pieData = {
    labels: ['Focus Time', 'Distraction Time', 'Absence Time'],
    datasets: [
      {
        data: [totalFocusTime, totalDistractionTime, totalAbsenceTime],
        backgroundColor: [
          'rgba(16, 185, 129, 0.8)',
          'rgba(239, 68, 68, 0.8)',
          'rgba(245, 158, 11, 0.8)'
        ],
        borderColor: 'rgba(30, 41, 59, 1)',
        borderWidth: 2,
      }
    ]
  };

  // Timeline Logic using Line Chart for logs
  const timelineData = {
    labels: logsData.map(l => new Date(l.timestamp).toLocaleTimeString()),
    datasets: [
      {
        label: 'State Timeline (Score over time)',
        data: logsData.map(l => l.focus_score),
        borderColor: '#10b981',
        stepped: true,
      }
    ]
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { labels: { color: '#f8fafc' } }
    },
    scales: {
      y: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' } },
      x: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' } }
    }
  };

  const pieOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { position: 'bottom', labels: { color: '#f8fafc' } }
    }
  };

  return (
    <div className="dashboard-layout animate-fade-in">
      <div className="sidebar">
        <h2>AI Study Planner</h2>
        
        <div className="user-info">
          <p style={{color: 'var(--text-muted)', fontSize: '0.9rem'}}>Logged in as</p>
          <p style={{fontSize: '1.2rem', fontWeight: '500'}}>{user.username}</p>
          <span style={{
            display: 'inline-block', 
            marginTop: '0.5rem', 
            padding: '0.2rem 0.5rem', 
            background: 'var(--accent)', 
            borderRadius: '4px',
            fontSize: '0.8rem'
          }}>
            {user.role.toUpperCase()}
          </span>
        </div>

        <div className="metrics-container">
          <div className="glass-panel metric-card">
            <span>Total Sessions</span>
            <h3>{totalSessions}</h3>
          </div>
          <div className="glass-panel metric-card">
            <span>Avg Focus Score</span>
            <h3 style={{color: 'var(--success)'}}>{avgScore}%</h3>
          </div>
          <div className="glass-panel metric-card">
            <span>Total Focus Mins</span>
            <h3>{totalFocusTime}</h3>
          </div>
        </div>

        {toastMessage && (
          <div style={{marginTop: '1rem', padding: '1rem', background: 'rgba(245, 158, 11, 0.2)', borderRadius: '8px', border: '1px solid #f59e0b'}}>
            <h4 style={{color: '#fcd34d'}}>⚠️ Posture Alert</h4>
            <p style={{fontSize: '0.9rem', color: '#fff', marginTop: '0.5rem'}}>{toastMessage}</p>
          </div>
        )}

        <div style={{marginTop: 'auto'}}>
          <button onClick={handleLogout} className="btn-outline" style={{width: '100%'}}>Sign Out</button>
        </div>
      </div>

      <div className="main-content">
        <div className="main-header">
          <h1>{user.role === 'developer' ? 'Global Analytics Hub' : 'Your Personal Dashboard'}</h1>
          <div className="status-indicator">
            <span style={{display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--success)', fontSize: '0.9rem'}}>
              <div style={{width: '8px', height: '8px', borderRadius: '50%', background: 'var(--success)'}}></div>
              Live Updating
            </span>
          </div>
        </div>

        {totalSessions === 0 && logsData.length === 0 ? (
          <div className="glass-panel" style={{padding: '3rem', textAlign: 'center'}}>
            <h2 style={{marginBottom: '1rem'}}>No Analytics Data Found</h2>
            <p style={{color: 'var(--text-muted)'}}>Start your camera app via the launcher to record your first study session!</p>
          </div>
        ) : (
          <>
            {totalSessions > 0 && (
              <div className="charts-grid">
                <div className="glass-panel chart-container">
                  <h3>Focus Score Trend</h3>
                  <div style={{flex: 1}}>
                    <Line data={lineData} options={chartOptions} />
                  </div>
                </div>
                <div className="glass-panel chart-container">
                  <h3>Time Distribution</h3>
                  <div style={{flex: 1}}>
                    <Pie data={pieData} options={pieOptions} />
                  </div>
                </div>
              </div>
            )}

            {logsData.length > 0 && (
              <div className="glass-panel chart-container" style={{height: '300px', marginBottom: '2rem'}}>
                <h3>Live Latest Session Tracker</h3>
                <div style={{flex: 1}}>
                  <Line data={timelineData} options={chartOptions} />
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default Dashboard;
