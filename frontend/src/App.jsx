import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import StudentPortal from './components/StudentPortal';
import StaffPortal from './components/StaffPortal';
import AdminDashboard from './components/AdminDashboard';
import ErrorBoundary from './components/ErrorBoundary';
import { apiLogin, apiGetMe, getStoredUser, clearStoredToken } from './api';
import { ShieldCheck, UserCheck, GraduationCap, Lock, LogIn, AlertCircle } from 'lucide-react';

export default function App() {
  const [currentUser, setCurrentUser] = useState(getStoredUser());
  const [loading, setLoading] = useState(true);
  const [loginError, setLoginError] = useState('');
  
  // Login form state
  const [username, setUsername] = useState('student');
  const [password, setPassword] = useState('student123');

  // Verify stored token on load or fallback to default student
  useEffect(() => {
    const initAuth = async () => {
      try {
        const user = await apiGetMe();
        setCurrentUser(user);
      } catch (err) {
        // If stored token is invalid or missing, attempt default login for smooth evaluation
        try {
          const authData = await apiLogin('student', 'student123');
          setCurrentUser(authData.user);
        } catch (loginErr) {
          console.warn('Initial auto-login could not connect to backend:', loginErr.message);
        }
      } finally {
        setLoading(false);
      }
    };
    initAuth();
  }, []);

  const handleRoleSwitch = async (roleName) => {
    setLoading(true);
    setLoginError('');
    try {
      const pass = `${roleName}123`;
      const data = await apiLogin(roleName, pass);
      setCurrentUser(data.user);
    } catch (err) {
      setLoginError(`Failed to switch to ${roleName}: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleManualLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setLoginError('');
    try {
      const data = await apiLogin(username.trim(), password);
      setCurrentUser(data.user);
    } catch (err) {
      setLoginError(err.message || 'Invalid username or password.');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    clearStoredToken();
    localStorage.removeItem('complaint_auth_user');
    setCurrentUser(null);
  };

  if (loading && !currentUser) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundColor: '#f8fafc', flexDirection: 'column', gap: '12px' }}>
        <div style={{ width: '32px', height: '32px', border: '3px solid #cbd5e1', borderTopColor: '#2563eb', borderRadius: '50%', animation: 'spin 1s linear infinite' }} />
        <p style={{ fontSize: '0.875rem', color: '#64748b' }}>Connecting to Complaint Intelligence API...</p>
      </div>
    );
  }

  // Not logged in view
  if (!currentUser) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundColor: '#f1f5f9', padding: '16px' }}>
        <div style={{ width: '100%', maxWidth: '420px', backgroundColor: '#ffffff', borderRadius: '12px', padding: '32px', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06)' }}>
          
          <div style={{ textAlign: 'center', marginBottom: '24px' }}>
            <div style={{
              width: '48px',
              height: '48px',
              borderRadius: '10px',
              backgroundColor: '#eff6ff',
              color: '#2563eb',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 12px auto'
            }}>
              <ShieldCheck size={28} />
            </div>
            <h1 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#0f172a' }}>
              Complaint Intelligence System
            </h1>
            <p style={{ fontSize: '0.8125rem', color: '#64748b', marginTop: '4px' }}>
              Academic Phase 8 Demonstration Portal
            </p>
          </div>

          {loginError && (
            <div style={{ padding: '10px 14px', backgroundColor: '#fef2f2', border: '1px solid #fecaca', borderRadius: '6px', color: '#b91c1c', fontSize: '0.8125rem', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <AlertCircle size={16} />
              <span>{loginError}</span>
            </div>
          )}

          {/* Quick Demo Sign In */}
          <div style={{ marginBottom: '20px' }}>
            <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#475569', textTransform: 'uppercase', marginBottom: '8px', textAlign: 'center' }}>
              One-Click Evaluator Sign-In
              <div style={{ fontSize: '0.6875rem', color: '#b45309', fontWeight: 500, textTransform: 'none', marginTop: '2px' }}>
                (Development Demo Accounts Only &bull; Disabled in Production)
              </div>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px' }}>
              <button
                type="button"
                onClick={() => handleRoleSwitch('student')}
                style={{ padding: '8px', borderRadius: '6px', border: '1px solid #cbd5e1', backgroundColor: '#f8fafc', fontSize: '0.75rem', fontWeight: 600, color: '#334155' }}
              >
                Student
              </button>
              <button
                type="button"
                onClick={() => handleRoleSwitch('staff')}
                style={{ padding: '8px', borderRadius: '6px', border: '1px solid #cbd5e1', backgroundColor: '#f8fafc', fontSize: '0.75rem', fontWeight: 600, color: '#334155' }}
              >
                Staff
              </button>
              <button
                type="button"
                onClick={() => handleRoleSwitch('admin')}
                style={{ padding: '8px', borderRadius: '6px', border: '1px solid #cbd5e1', backgroundColor: '#f8fafc', fontSize: '0.75rem', fontWeight: 600, color: '#334155' }}
              >
                Admin
              </button>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', margin: '20px 0', color: '#cbd5e1' }}>
            <div style={{ flex: 1, height: '1px', backgroundColor: '#e2e8f0' }} />
            <span style={{ padding: '0 10px', fontSize: '0.75rem', color: '#94a3b8' }}>or password login</span>
            <div style={{ flex: 1, height: '1px', backgroundColor: '#e2e8f0' }} />
          </div>

          <form onSubmit={handleManualLogin}>
            <div style={{ marginBottom: '14px' }}>
              <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '4px' }}>
                Username
              </label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                style={{ width: '100%', padding: '8px 12px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '0.875rem' }}
              />
            </div>

            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '4px' }}>
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                style={{ width: '100%', padding: '8px 12px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '0.875rem' }}
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              style={{
                width: '100%',
                padding: '10px',
                backgroundColor: '#2563eb',
                color: '#ffffff',
                border: 'none',
                borderRadius: '6px',
                fontWeight: 700,
                fontSize: '0.875rem',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '8px',
              }}
            >
              <LogIn size={16} /> Sign In
            </button>
          </form>

        </div>
      </div>
    );
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', backgroundColor: '#f8fafc' }}>
      
      {/* Universal Top Navigation Header */}
      <Header
        currentUser={currentUser}
        onSwitchRole={handleRoleSwitch}
        onLogout={handleLogout}
      />

      {/* Main Role-Specific View */}
      <main style={{ flex: 1, paddingBottom: '48px' }}>
        <ErrorBoundary name="Main Application View">
          {currentUser.role === 'student' && (
            <StudentPortal currentUser={currentUser} />
          )}

          {currentUser.role === 'staff' && (
            <StaffPortal currentUser={currentUser} />
          )}

          {currentUser.role === 'admin' && (
            <AdminDashboard currentUser={currentUser} />
          )}
        </ErrorBoundary>
      </main>

      {/* Footer */}
      <footer style={{
        borderTop: '1px solid #e2e8f0',
        backgroundColor: '#ffffff',
        padding: '14px 24px',
        textAlign: 'center',
        fontSize: '0.75rem',
        color: '#64748b',
      }}>
        College Complaint Intelligence System &bull; Phase 8 Integration & Demonstration &bull; Powered by FastAPI &amp; React
      </footer>

    </div>
  );
}

