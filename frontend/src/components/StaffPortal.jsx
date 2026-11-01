import React, { useState, useEffect } from 'react';
import { 
  AlertTriangle, CheckCircle, ShieldAlert, 
  Search, RefreshCw, Eye
} from 'lucide-react';
import { apiListComplaints, apiUpdateComplaintStatus } from '../api';
import { 
  formatPercent, safeArray, safeString, 
  normalizePriority, normalizeStatus 
} from '../utils/formatters';
import ComplaintDetailModal from './ComplaintDetailModal';
import ErrorBoundary from './ErrorBoundary';

const CATEGORY_NAMES = {
  C01: 'Hostel and Accommodation',
  C02: 'Electricity and Water',
  C03: 'Internet and Network',
  C04: 'Mess and Food',
  C05: 'Academic and Examination',
  C06: 'Classroom and Laboratory',
  C07: 'Sanitation and Cleanliness',
  C08: 'Campus Safety',
  C09: 'Transportation',
  C10: 'Administrative Services',
  C11: 'Other / Unclassified',
};

const PRIORITY_COLORS = {
  critical: { bg: '#fef2f2', border: '#fca5a5', text: '#b91c1c' },
  high: { bg: '#fff7ed', border: '#fdba74', text: '#c2410c' },
  medium: { bg: '#fefce8', border: '#fde047', text: '#a16207' },
  low: { bg: '#f0fdf4', border: '#86efac', text: '#15803d' },
};

const STATUS_COLORS = {
  submitted: { bg: '#f1f5f9', text: '#475569' },
  in_progress: { bg: '#fef3c7', text: '#b45309' },
  resolved: { bg: '#dcfce7', text: '#15803d' },
  rejected: { bg: '#fee2e2', text: '#b91c1c' },
};

export default function StaffPortal({ currentUser }) {
  const [complaints, setComplaints] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [selectedComplaintId, setSelectedComplaintId] = useState(null);

  // Filters
  const [statusFilter, setStatusFilter] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [priorityFilter, setPriorityFilter] = useState('');
  const [needsReviewOnly, setNeedsReviewOnly] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  const fetchComplaints = async () => {
    setLoading(true);
    setError('');
    try {
      const filters = {};
      if (statusFilter) filters.status = statusFilter;
      if (categoryFilter) filters.category = categoryFilter;
      if (priorityFilter) filters.priority = priorityFilter;
      if (needsReviewOnly) filters.needs_review = true;

      const data = await apiListComplaints(filters);
      setComplaints(safeArray(data));
    } catch (err) {
      console.error('Failed to fetch complaint queue:', err);
      setError(err.message || 'Failed to load complaint queue');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchComplaints();
  }, [statusFilter, categoryFilter, priorityFilter, needsReviewOnly]);

  const handleQuickStatusChange = async (complaintId, newStatus) => {
    try {
      await apiUpdateComplaintStatus(complaintId, newStatus);
      fetchComplaints();
    } catch (err) {
      alert(`Failed to update status: ${err.message}`);
    }
  };

  // Client-side text search filter
  const filteredComplaints = complaints.filter((c) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    const textMatch = (c?.complaint_text || '').toLowerCase().includes(q);
    const locMatch = (c?.location || '').toLowerCase().includes(q);
    const idMatch = String(c?.id || '').toLowerCase().includes(q);
    return textMatch || locMatch || idMatch;
  });

  // Calculate quick stats safely
  const totalCount = complaints.length;
  const reviewCount = complaints.filter((c) => Boolean(c?.needs_human_review)).length;
  const criticalCount = complaints.filter((c) => {
    const p = normalizePriority(c?.final_priority);
    return p === 'critical' || p === 'high';
  }).length;
  const resolvedCount = complaints.filter((c) => normalizeStatus(c?.status) === 'resolved').length;

  return (
    <ErrorBoundary name="Staff Review Queue">
      <div style={{ maxWidth: '1280px', margin: '0 auto', padding: '24px 16px' }}>
        
        {/* Header and Summary */}
        <div style={{ marginBottom: '20px' }}>
          <h2 style={{ fontSize: '1.375rem', fontWeight: 800, color: '#0f172a' }}>
            Department Incident Triage & Queue
          </h2>
          <p style={{ fontSize: '0.875rem', color: '#64748b' }}>
            Evaluate model-suggested routing, review low-confidence classifications, and execute governed priority overrides.
          </p>
        </div>

        {error && (
          <div style={{ padding: '12px 16px', backgroundColor: '#fef2f2', border: '1px solid #fecaca', borderRadius: '8px', color: '#b91c1c', fontSize: '0.875rem', marginBottom: '20px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div><strong>Error loading queue:</strong> {error}</div>
            <button onClick={fetchComplaints} style={{ backgroundColor: '#b91c1c', color: '#fff', border: 'none', padding: '4px 10px', borderRadius: '4px', fontSize: '0.75rem', cursor: 'pointer' }}>Retry</button>
          </div>
        )}

        {/* Summary KPI Cards */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '14px', marginBottom: '20px' }}>
          <div style={{ backgroundColor: '#ffffff', padding: '16px', borderRadius: '10px', border: '1px solid #e2e8f0', boxShadow: '0 1px 2px rgba(0,0,0,0.04)' }}>
            <div style={{ fontSize: '0.75rem', fontWeight: 600, color: '#64748b' }}>Total in Active View</div>
            <div style={{ fontSize: '1.5rem', fontWeight: 800, color: '#0f172a', marginTop: '4px' }}>{totalCount}</div>
          </div>

          <div style={{ backgroundColor: '#ffffff', padding: '16px', borderRadius: '10px', border: '1px solid #e2e8f0', boxShadow: '0 1px 2px rgba(0,0,0,0.04)' }}>
            <div style={{ fontSize: '0.75rem', fontWeight: 600, color: '#b45309', display: 'flex', alignItems: 'center', gap: '4px' }}>
              <AlertTriangle size={14} /> Low-Confidence / Needs Review
            </div>
            <div style={{ fontSize: '1.5rem', fontWeight: 800, color: '#b45309', marginTop: '4px' }}>{reviewCount}</div>
          </div>

          <div style={{ backgroundColor: '#ffffff', padding: '16px', borderRadius: '10px', border: '1px solid #e2e8f0', boxShadow: '0 1px 2px rgba(0,0,0,0.04)' }}>
            <div style={{ fontSize: '0.75rem', fontWeight: 600, color: '#b91c1c', display: 'flex', alignItems: 'center', gap: '4px' }}>
              <ShieldAlert size={14} /> High / Critical Priority
            </div>
            <div style={{ fontSize: '1.5rem', fontWeight: 800, color: '#b91c1c', marginTop: '4px' }}>{criticalCount}</div>
          </div>

          <div style={{ backgroundColor: '#ffffff', padding: '16px', borderRadius: '10px', border: '1px solid #e2e8f0', boxShadow: '0 1px 2px rgba(0,0,0,0.04)' }}>
            <div style={{ fontSize: '0.75rem', fontWeight: 600, color: '#15803d', display: 'flex', alignItems: 'center', gap: '4px' }}>
              <CheckCircle size={14} /> Resolved Incidents
            </div>
            <div style={{ fontSize: '1.5rem', fontWeight: 800, color: '#15803d', marginTop: '4px' }}>{resolvedCount}</div>
          </div>
        </div>

        {/* Filter and Search Bar */}
        <div style={{
          backgroundColor: '#ffffff',
          padding: '16px',
          borderRadius: '10px',
          border: '1px solid #e2e8f0',
          marginBottom: '20px',
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '12px',
        }}>
          {/* Search */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', minWidth: '240px', flex: 1 }}>
            <Search size={16} color="#94a3b8" />
            <input
              type="text"
              placeholder="Search complaint text, location, or ID..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{
                width: '100%',
                padding: '8px 12px',
                border: '1px solid #cbd5e1',
                borderRadius: '6px',
                fontSize: '0.875rem',
              }}
            />
          </div>

          {/* Filters */}
          <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: '10px' }}>
            
            {/* Status */}
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              style={{ padding: '8px 12px', border: '1px solid #cbd5e1', borderRadius: '6px', fontSize: '0.8125rem', backgroundColor: '#fff' }}
            >
              <option value="">All Statuses</option>
              <option value="submitted">Submitted</option>
              <option value="in_progress">In Progress</option>
              <option value="resolved">Resolved</option>
              <option value="rejected">Rejected</option>
            </select>

            {/* Category */}
            <select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              style={{ padding: '8px 12px', border: '1px solid #cbd5e1', borderRadius: '6px', fontSize: '0.8125rem', backgroundColor: '#fff' }}
            >
              <option value="">All Categories</option>
              {Object.entries(CATEGORY_NAMES).map(([code, name]) => (
                <option key={code} value={code}>{code}: {name}</option>
              ))}
            </select>

            {/* Priority */}
            <select
              value={priorityFilter}
              onChange={(e) => setPriorityFilter(e.target.value)}
              style={{ padding: '8px 12px', border: '1px solid #cbd5e1', borderRadius: '6px', fontSize: '0.8125rem', backgroundColor: '#fff' }}
            >
              <option value="">All Priorities</option>
              <option value="CRITICAL">Critical</option>
              <option value="HIGH">High</option>
              <option value="MEDIUM">Medium</option>
              <option value="LOW">Low</option>
            </select>

            {/* Needs Review Toggle */}
            <label style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              fontSize: '0.8125rem',
              fontWeight: 600,
              color: needsReviewOnly ? '#b45309' : '#475569',
              backgroundColor: needsReviewOnly ? '#fef3c7' : '#f1f5f9',
              padding: '7px 12px',
              borderRadius: '6px',
              cursor: 'pointer',
            }}>
              <input
                type="checkbox"
                checked={needsReviewOnly}
                onChange={(e) => setNeedsReviewOnly(e.target.checked)}
                style={{ cursor: 'pointer' }}
              />
              Needs Review Only
            </label>

            {/* Refresh */}
            <button
              onClick={fetchComplaints}
              disabled={loading}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '8px 14px',
                backgroundColor: '#f1f5f9',
                color: '#334155',
                border: 'none',
                borderRadius: '6px',
                fontSize: '0.8125rem',
                fontWeight: 600,
                cursor: loading ? 'not-allowed' : 'pointer',
              }}
            >
              <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
              Refresh
            </button>

          </div>
        </div>

        {/* Tickets Table */}
        <div style={{ backgroundColor: '#ffffff', borderRadius: '10px', border: '1px solid #e2e8f0', overflow: 'hidden', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
          {loading ? (
            <div style={{ textAlign: 'center', padding: '48px', color: '#64748b' }}>
              Loading queue...
            </div>
          ) : filteredComplaints.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '48px 16px', color: '#94a3b8' }}>
              <p style={{ fontSize: '1rem', fontWeight: 600 }}>No complaints match the selected filters.</p>
              <p style={{ fontSize: '0.8125rem', marginTop: '4px' }}>Try resetting filters or adjusting search parameters.</p>
            </div>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.875rem' }}>
                <thead>
                  <tr style={{ backgroundColor: '#f8fafc', borderBottom: '2px solid #e2e8f0', color: '#475569', fontSize: '0.75rem', textTransform: 'uppercase' }}>
                    <th style={{ padding: '12px 14px' }}>Ticket ID</th>
                    <th style={{ padding: '12px 14px' }}>Location</th>
                    <th style={{ padding: '12px 14px' }}>Description Preview</th>
                    <th style={{ padding: '12px 14px' }}>AI Route & Confidence</th>
                    <th style={{ padding: '12px 14px' }}>Priority</th>
                    <th style={{ padding: '12px 14px' }}>Status</th>
                    <th style={{ padding: '12px 14px', textAlign: 'right' }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredComplaints.map((c) => {
                    const prioKey = normalizePriority(c?.final_priority);
                    const prioSt = PRIORITY_COLORS[prioKey] || PRIORITY_COLORS.medium;
                    const statKey = normalizeStatus(c?.status);
                    const statSt = STATUS_COLORS[statKey] || STATUS_COLORS.submitted;
                    const isReview = Boolean(c?.needs_human_review);
                    const catDisplay = safeString(c?.category_name || c?.predicted_category, '—');

                    return (
                      <tr key={c.id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                        <td style={{ padding: '14px', fontFamily: 'monospace', fontWeight: 700, color: '#0f172a' }}>
                          {c.id}
                        </td>
                        <td style={{ padding: '14px', color: '#475569', maxWidth: '140px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          {safeString(c.location)}
                        </td>
                        <td style={{ padding: '14px', maxWidth: '280px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          {c.complaint_text}
                        </td>
                        <td style={{ padding: '14px' }}>
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                            <span style={{ fontWeight: 600, color: '#1e293b', fontSize: '0.8125rem' }}>
                              {catDisplay}
                            </span>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                              <span style={{ fontSize: '0.75rem', color: '#64748b' }}>
                                {formatPercent(c.confidence)}
                              </span>
                              {isReview && (
                                <span style={{ fontSize: '0.6875rem', fontWeight: 700, backgroundColor: '#fef3c7', color: '#b45309', padding: '1px 5px', borderRadius: '4px' }}>
                                  Review Req.
                                </span>
                              )}
                            </div>
                          </div>
                        </td>
                        <td style={{ padding: '14px' }}>
                          <span style={{
                            fontSize: '0.75rem',
                            fontWeight: 700,
                            textTransform: 'uppercase',
                            padding: '2px 8px',
                            borderRadius: '9999px',
                            backgroundColor: prioSt.bg,
                            color: prioSt.text,
                            display: 'inline-block',
                            width: 'fit-content',
                            border: `1px solid ${prioSt.border}`
                          }}>
                            {prioKey}
                          </span>
                        </td>
                        <td style={{ padding: '14px' }}>
                          <select
                            value={statKey}
                            onChange={(e) => handleQuickStatusChange(c.id, e.target.value)}
                            style={{
                              fontSize: '0.75rem',
                              fontWeight: 600,
                              padding: '4px 8px',
                              borderRadius: '6px',
                              border: '1px solid #cbd5e1',
                              backgroundColor: statSt.bg,
                              color: statSt.text,
                              cursor: 'pointer',
                            }}
                          >
                            <option value="submitted">Submitted</option>
                            <option value="in_progress">In Progress</option>
                            <option value="resolved">Resolved</option>
                            <option value="rejected">Rejected</option>
                          </select>
                        </td>
                        <td style={{ padding: '14px', textAlign: 'right' }}>
                          <button
                            onClick={() => setSelectedComplaintId(c.id)}
                            style={{
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: '4px',
                              backgroundColor: '#2563eb',
                              color: '#ffffff',
                              border: 'none',
                              padding: '6px 12px',
                              borderRadius: '6px',
                              fontSize: '0.8125rem',
                              fontWeight: 600,
                              cursor: 'pointer',
                            }}
                          >
                            <Eye size={14} /> Inspect & Triage
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Detail Modal */}
        {selectedComplaintId && (
          <ComplaintDetailModal
            complaintId={selectedComplaintId}
            currentUser={currentUser}
            onClose={() => setSelectedComplaintId(null)}
            onRefresh={fetchComplaints}
          />
        )}

      </div>
    </ErrorBoundary>
  );
}
