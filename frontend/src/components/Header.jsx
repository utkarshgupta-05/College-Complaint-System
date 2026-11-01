import React from 'react';
import { ShieldCheck, UserCheck, Wrench, GraduationCap, LogOut } from 'lucide-react';

export default function Header({ currentUser, onSwitchRole, onLogout }) {
  const roles = [
    { id: 'student', label: 'Student Portal', icon: GraduationCap, user: 'student', desc: 'Submit & Track' },
    { id: 'staff', label: 'Staff Review', icon: Wrench, user: 'staff', desc: 'Triage & Override' },
    { id: 'admin', label: 'Admin Analytics', icon: ShieldCheck, user: 'admin', desc: 'Hotspots & Patterns' },
  ];

  return (
    <header style={{
      backgroundColor: '#ffffff',
      borderBottom: '1px solid #e2e8f0',
      padding: '12px 24px',
      position: 'sticky',
      top: 0,
      zIndex: 40,
      boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.05)'
    }}>
      <div style={{ maxWidth: '1280px', margin: '0 auto', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
        
        {/* Title */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{
            background: 'linear-gradient(135deg, #2563eb, #1d4ed8)',
            color: '#fff',
            padding: '8px',
            borderRadius: '8px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <ShieldCheck size={22} />
          </div>
          <div>
            <h1 style={{ fontSize: '1.125rem', fontWeight: 700, color: '#0f172a', letterSpacing: '-0.025em' }}>
              College Complaint Intelligence System
            </h1>
            <p style={{ fontSize: '0.75rem', color: '#64748b' }}>
              Phase 8 Automated Routing &bull; Priority Triage &bull; Pattern Discovery
            </p>
          </div>
        </div>

        {/* Role Switcher */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', backgroundColor: '#f1f5f9', padding: '4px', borderRadius: '10px' }}>
          {roles.map((r) => {
            const Icon = r.icon;
            const isActive = currentUser?.role === r.id;
            return (
              <button
                key={r.id}
                onClick={() => onSwitchRole(r.user)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '6px 12px',
                  fontSize: '0.8125rem',
                  fontWeight: 600,
                  border: 'none',
                  borderRadius: '6px',
                  transition: 'all 0.15s ease',
                  backgroundColor: isActive ? '#ffffff' : 'transparent',
                  color: isActive ? '#2563eb' : '#475569',
                  boxShadow: isActive ? '0 1px 2px 0 rgba(0, 0, 0, 0.08)' : 'none',
                }}
              >
                <Icon size={15} />
                <span>{r.label}</span>
              </button>
            );
          })}
        </div>

        {/* User Info */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: '0.875rem', fontWeight: 600, color: '#1e293b' }}>
              {currentUser?.full_name || currentUser?.username}
            </div>
            <div style={{ fontSize: '0.75rem', color: '#64748b', textTransform: 'capitalize' }}>
              Role: <strong style={{ color: '#2563eb' }}>{currentUser?.role}</strong> {currentUser?.department ? `• ${currentUser.department}` : ''}
            </div>
          </div>
        </div>

      </div>
    </header>
  );
}

