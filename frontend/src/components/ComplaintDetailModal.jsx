import React, { useState, useEffect } from 'react';
import { 
  X, AlertTriangle, CheckCircle, ShieldAlert, 
  Layers, BarChart2, FileText, ArrowRight, UserCheck, 
  Copy, MapPin, Calendar, Tag, RefreshCw
} from 'lucide-react';
import { apiGetComplaintDetail, apiUpdateComplaintStatus, apiOverridePriority, apiOverrideCategory } from '../api';
import { 
  formatNumber, formatPercent, formatDate, safeArray, 
  safeObject, safeString, normalizePriority, normalizeStatus 
} from '../utils/formatters';
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

export default function ComplaintDetailModal({ complaintId, complaint: initialComplaint, currentUser, onClose, onRefresh }) {
  const [complaint, setComplaint] = useState(initialComplaint || null);
  const [loading, setLoading] = useState(!initialComplaint || !initialComplaint.prediction);
  const [fetchError, setFetchError] = useState('');

  const [newStatus, setNewStatus] = useState(initialComplaint?.status || 'submitted');
  const [overridePriority, setOverridePriority] = useState('HIGH');
  const [overrideReason, setOverrideReason] = useState('');
  const [overrideCategory, setOverrideCategory] = useState(initialComplaint?.prediction?.predicted_category || 'C01');
  const [updatingCategory, setUpdatingCategory] = useState(false);
  const [updating, setUpdating] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  const idToLoad = complaintId || initialComplaint?.id;

  // Fetch full complaint detail if missing or on mount
  const loadDetail = async () => {
    if (!idToLoad) return;
    setLoading(true);
    setFetchError('');
    try {
      const data = await apiGetComplaintDetail(idToLoad);
      setComplaint(data);
      setNewStatus(data.status);
      const currentPrio = data.priority?.final_priority || 'MEDIUM';
      setOverridePriority(currentPrio.toUpperCase());
      if (data.prediction?.predicted_category) {
        setOverrideCategory(data.prediction.predicted_category);
      }
    } catch (err) {
      console.error('Failed to load complaint details:', err);
      setFetchError(err.message || 'Failed to load ticket details.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDetail();
  }, [idToLoad]);

  if (!idToLoad) return null;

  const isStaffOrAdmin = currentUser?.role === 'staff' || currentUser?.role === 'admin';

  const pred = complaint?.prediction || null;
  const prio = complaint?.priority || null;
  const duplicates = safeArray(complaint?.duplicate_suggestions || complaint?.duplicates);
  const overrides = safeArray(complaint?.priority_overrides || complaint?.overrides);

  const effectivePrioKey = normalizePriority(prio?.final_priority || prio?.suggested_priority || complaint?.final_priority);
  const prioStyle = PRIORITY_COLORS[effectivePrioKey] || PRIORITY_COLORS.medium;
  const statusKey = normalizeStatus(complaint?.status || newStatus);
  const statusStyle = STATUS_COLORS[statusKey] || STATUS_COLORS.submitted;

  const handleStatusChange = async (e) => {
    const status = e.target.value;
    setNewStatus(status);
    setUpdating(true);
    setErrorMessage('');
    setSuccessMessage('');
    try {
      const updated = await apiUpdateComplaintStatus(complaint.id, status);
      setComplaint(updated);
      setSuccessMessage(`Status updated to ${status.replace('_', ' ')}.`);
      if (onRefresh) onRefresh();
    } catch (err) {
      setErrorMessage(err.message);
    } finally {
      setUpdating(false);
    }
  };

  const handlePriorityOverride = async (e) => {
    e.preventDefault();
    if (!overrideReason.trim()) {
      setErrorMessage('A justified override reason is required.');
      return;
    }
    setUpdating(true);
    setErrorMessage('');
    setSuccessMessage('');
    try {
      const updated = await apiOverridePriority(complaint.id, overridePriority, overrideReason.trim());
      setComplaint(updated);
      setSuccessMessage(`Priority overridden to ${overridePriority.toUpperCase()} successfully.`);
      setOverrideReason('');
      if (onRefresh) onRefresh();
    } catch (err) {
      setErrorMessage(err.message);
    } finally {
      setUpdating(false);
    }
  };

  const handleCategoryOverride = async (categoryToSet, reasonToUse) => {
    setUpdatingCategory(true);
    setErrorMessage('');
    setSuccessMessage('');
    try {
      const updated = await apiOverrideCategory(complaint.id, categoryToSet, reasonToUse || 'Staff category review');
      setComplaint(updated);
      setOverrideCategory(categoryToSet);
      setSuccessMessage(`Category updated to ${categoryToSet}: ${CATEGORY_NAMES[categoryToSet] || categoryToSet}. Review flag cleared.`);
      if (onRefresh) onRefresh();
    } catch (err) {
      setErrorMessage(err.message);
    } finally {
      setUpdatingCategory(false);
    }
  };

  return (
    <ErrorBoundary name="Complaint Detail Modal">
      <div style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(15, 23, 42, 0.65)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 50,
        padding: '16px',
        backdropFilter: 'blur(3px)',
      }}>
        <div style={{
          backgroundColor: '#ffffff',
          borderRadius: '14px',
          width: '100%',
          maxWidth: '860px',
          maxHeight: '90vh',
          display: 'flex',
          flexDirection: 'column',
          boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.2), 0 10px 10px -5px rgba(0, 0, 0, 0.08)',
          overflow: 'hidden',
        }}>
          {/* Modal Header */}
          <div style={{
            padding: '18px 24px',
            borderBottom: '1px solid #e2e8f0',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            backgroundColor: '#f8fafc',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <span style={{
                fontFamily: 'monospace',
                fontSize: '0.95rem',
                fontWeight: 700,
                color: '#1e293b',
                backgroundColor: '#e2e8f0',
                padding: '4px 8px',
                borderRadius: '6px',
              }}>
                {complaint?.id || idToLoad}
              </span>
              <span style={{
                fontSize: '0.75rem',
                fontWeight: 700,
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
                padding: '4px 10px',
                borderRadius: '9999px',
                backgroundColor: statusStyle.bg,
                color: statusStyle.text,
              }}>
                {statusKey.replace('_', ' ')}
              </span>
              <span style={{
                fontSize: '0.75rem',
                fontWeight: 700,
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
                padding: '4px 10px',
                borderRadius: '9999px',
                backgroundColor: prioStyle.bg,
                color: prioStyle.text,
                border: `1px solid ${prioStyle.border}`,
              }}>
                {effectivePrioKey} Priority {overrides.length > 0 ? '(Overridden)' : ''}
              </span>
            </div>

            <button
              onClick={onClose}
              style={{
                border: 'none',
                background: 'transparent',
                color: '#64748b',
                padding: '6px',
                borderRadius: '6px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
              }}
            >
              <X size={20} />
            </button>
          </div>

          {/* Modal Content - Scrollable */}
          <div style={{ padding: '24px', overflowY: 'auto', flex: 1, display: 'flex', flexDirection: 'column', gap: '20px' }}>
            
            {loading && !complaint && (
              <div style={{ textAlign: 'center', padding: '40px', color: '#64748b' }}>
                <RefreshCw size={24} className="animate-spin" style={{ margin: '0 auto 8px auto' }} />
                <p>Loading full ticket explainability...</p>
              </div>
            )}

            {fetchError && (
              <div style={{ padding: '12px 16px', backgroundColor: '#fef2f2', border: '1px solid #fecaca', borderRadius: '8px', color: '#b91c1c', fontSize: '0.875rem' }}>
                <strong>Error:</strong> {fetchError}
              </div>
            )}

            {errorMessage && (
              <div style={{ padding: '12px 16px', backgroundColor: '#fef2f2', border: '1px solid #fecaca', borderRadius: '8px', color: '#b91c1c', fontSize: '0.875rem' }}>
                <strong>Error:</strong> {errorMessage}
              </div>
            )}
            {successMessage && (
              <div style={{ padding: '12px 16px', backgroundColor: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: '8px', color: '#15803d', fontSize: '0.875rem' }}>
                <strong>Success:</strong> {successMessage}
              </div>
            )}

            {complaint && (
              <>
                {/* Metadata Cards */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px' }}>
                  <div style={{ padding: '10px 14px', backgroundColor: '#f8fafc', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
                    <div style={{ fontSize: '0.75rem', color: '#64748b', display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <Calendar size={14} /> Created
                    </div>
                    <div style={{ fontSize: '0.875rem', fontWeight: 600, color: '#1e293b', marginTop: '4px' }}>
                      {formatDate(complaint.created_at)}
                    </div>
                  </div>

                  <div style={{ padding: '10px 14px', backgroundColor: '#f8fafc', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
                    <div style={{ fontSize: '0.75rem', color: '#64748b', display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <MapPin size={14} /> Location
                    </div>
                    <div style={{ fontSize: '0.875rem', fontWeight: 600, color: '#1e293b', marginTop: '4px' }}>
                      {safeString(complaint.location, 'General Campus')}
                    </div>
                  </div>

                  <div style={{ padding: '10px 14px', backgroundColor: '#f8fafc', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
                    <div style={{ fontSize: '0.75rem', color: '#64748b', display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <Tag size={14} /> Submitter
                    </div>
                    <div style={{ fontSize: '0.875rem', fontWeight: 600, color: '#1e293b', marginTop: '4px' }}>
                      {complaint.student_username || `User #${complaint.user_id}`} {complaint.student_dept ? `(${complaint.student_dept})` : ''}
                    </div>
                  </div>
                </div>

                {/* Full Complaint Text */}
                <div style={{ backgroundColor: '#ffffff', borderRadius: '8px', border: '1px solid #e2e8f0', padding: '16px' }}>
                  <div style={{ fontSize: '0.8125rem', fontWeight: 700, color: '#475569', textTransform: 'uppercase', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <FileText size={16} color="#2563eb" /> Complaint Description
                  </div>
                  <p style={{ fontSize: '0.95rem', color: '#1e293b', lineHeight: 1.6, whiteSpace: 'pre-wrap', backgroundColor: '#f8fafc', padding: '12px', borderRadius: '6px', borderLeft: '4px solid #2563eb' }}>
                    {complaint.complaint_text}
                  </p>
                </div>

                {/* AI Explainability Section */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '16px' }}>
                  
                  {/* Category Probability Distribution */}
                  <div style={{ backgroundColor: '#ffffff', borderRadius: '10px', border: '1px solid #e2e8f0', padding: '16px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
                      <div style={{ fontSize: '0.875rem', fontWeight: 700, color: '#1e293b', display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <Layers size={18} color="#2563eb" /> AI Category Routing
                      </div>
                      {pred?.needs_human_review || pred?.low_confidence ? (
                        <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#b45309', backgroundColor: '#fef3c7', padding: '2px 8px', borderRadius: '4px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                          <AlertTriangle size={12} /> Needs Human Review
                        </span>
                      ) : (
                        <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#15803d', backgroundColor: '#dcfce7', padding: '2px 8px', borderRadius: '4px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                          <CheckCircle size={12} /> Confident Route
                        </span>
                      )}
                    </div>

                    <div style={{ marginBottom: '12px', padding: '10px', backgroundColor: '#f1f5f9', borderRadius: '8px' }}>
                      <div style={{ fontSize: '0.75rem', color: '#64748b' }}>Assigned Category</div>
                      <div style={{ fontSize: '1rem', fontWeight: 700, color: '#0f172a' }}>
                        {pred?.predicted_category || 'C11'}: {safeString(pred?.category_name || CATEGORY_NAMES[pred?.predicted_category], 'General')}
                      </div>
                      {complaint?.assigned_department && (
                        <div style={{ fontSize: '0.75rem', color: '#475569', marginTop: '2px' }}>
                          Department: <strong>{complaint.assigned_department}</strong>
                        </div>
                      )}
                      <div style={{ fontSize: '0.8125rem', color: '#475569', marginTop: '2px' }}>
                        Calibrated Confidence: <strong>{formatPercent(pred?.confidence ?? pred?.confidence_score)}</strong> (Threshold: 60%)
                      </div>
                    </div>

                    {/* Staff Category Governance & Review Resolution */}
                    {isStaffOrAdmin && (
                      <div style={{ marginBottom: '14px', padding: '10px 12px', backgroundColor: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '8px' }}>
                        <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#334155', marginBottom: '8px' }}>
                          Staff Category Triage &amp; Human Review:
                        </div>

                        {pred?.needs_human_review && (
                          <button
                            type="button"
                            disabled={updatingCategory}
                            onClick={() => handleCategoryOverride(pred.predicted_category, 'Staff accepted and confirmed model prediction')}
                            style={{
                              width: '100%',
                              padding: '6px 12px',
                              backgroundColor: '#dcfce7',
                              color: '#15803d',
                              border: '1px solid #bbf7d0',
                              borderRadius: '6px',
                              fontSize: '0.75rem',
                              fontWeight: 600,
                              cursor: 'pointer',
                              marginBottom: '8px',
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              gap: '6px',
                            }}
                          >
                            <CheckCircle size={14} /> Accept &amp; Confirm Suggested Category ({pred.predicted_category})
                          </button>
                        )}

                        <div style={{ display: 'flex', gap: '8px' }}>
                          <select
                            value={overrideCategory}
                            onChange={(e) => setOverrideCategory(e.target.value)}
                            style={{ flex: 1, padding: '6px 10px', fontSize: '0.75rem', borderRadius: '6px', border: '1px solid #cbd5e1', backgroundColor: '#fff' }}
                          >
                            {Object.entries(CATEGORY_NAMES).map(([code, name]) => (
                              <option key={code} value={code}>{code}: {name}</option>
                            ))}
                          </select>
                          <button
                            type="button"
                            disabled={updatingCategory}
                            onClick={() => handleCategoryOverride(overrideCategory, 'Staff corrected category during review')}
                            style={{
                              padding: '6px 12px',
                              backgroundColor: '#2563eb',
                              color: '#fff',
                              border: 'none',
                              borderRadius: '6px',
                              fontSize: '0.75rem',
                              fontWeight: 600,
                              cursor: 'pointer',
                            }}
                          >
                            {updatingCategory ? 'Updating...' : 'Correct Category'}
                          </button>
                        </div>
                      </div>
                    )}

                    {/* Probabilities Bars */}
                    {pred?.all_scores && Object.keys(pred.all_scores).length > 0 && (
                      <div>
                        <div style={{ fontSize: '0.75rem', fontWeight: 600, color: '#64748b', marginBottom: '8px' }}>
                          Top Class Probabilities (Calibrated Linear SVM)
                        </div>
                        {Object.entries(pred.all_scores)
                          .sort(([, a], [, b]) => Number(b) - Number(a))
                          .slice(0, 4)
                          .map(([cat, prob]) => {
                            const numProb = Number(prob) || 0;
                            return (
                              <div key={cat} style={{ marginBottom: '8px' }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', marginBottom: '2px' }}>
                                  <span style={{ fontWeight: cat === pred?.predicted_category ? 700 : 500, color: cat === pred?.predicted_category ? '#2563eb' : '#334155' }}>
                                    {cat} - {CATEGORY_NAMES[cat] || cat}
                                  </span>
                                  <span style={{ fontWeight: 600, color: '#475569' }}>
                                    {formatPercent(numProb)}
                                  </span>
                                </div>
                                <div style={{ height: '6px', width: '100%', backgroundColor: '#f1f5f9', borderRadius: '3px', overflow: 'hidden' }}>
                                  <div style={{
                                    height: '100%',
                                    width: `${Math.min(100, Math.max(2, (numProb > 1 ? numProb : numProb * 100)))}%`,
                                    backgroundColor: cat === pred?.predicted_category ? '#2563eb' : '#94a3b8',
                                    borderRadius: '3px',
                                  }} />
                                </div>
                              </div>
                            );
                          })}
                      </div>
                    )}
                  </div>

                  {/* Priority Scoring Breakdown */}
                  <div style={{ backgroundColor: '#ffffff', borderRadius: '10px', border: '1px solid #e2e8f0', padding: '16px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
                      <div style={{ fontSize: '0.875rem', fontWeight: 700, color: '#1e293b', display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <BarChart2 size={18} color="#2563eb" /> Priority Score Signals
                      </div>
                      <div style={{
                        fontSize: '0.95rem',
                        fontWeight: 800,
                        color: prioStyle.text,
                        backgroundColor: prioStyle.bg,
                        padding: '2px 8px',
                        borderRadius: '6px',
                        border: `1px solid ${prioStyle.border}`
                      }}>
                        {formatNumber(prio?.score ?? prio?.priority_score, 1)} / 100
                      </div>
                    </div>

                    <div style={{ fontSize: '0.75rem', color: '#64748b', marginBottom: '12px' }}>
                      Formula: P = min(100, 0.35×Sev + 0.25×Safe + 0.20×Pop + 0.10×Wait + 0.10×Recur)
                    </div>

                    {prio?.signals && Object.keys(prio.signals).length > 0 && (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                        {Object.entries(prio.signals).map(([sigKey, sigVal]) => (
                          <div key={sigKey} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '6px 10px', backgroundColor: '#f8fafc', borderRadius: '6px' }}>
                            <span style={{ fontSize: '0.8125rem', color: '#334155', textTransform: 'capitalize' }}>
                              {sigKey.replace(/_/g, ' ')}
                            </span>
                            <strong style={{ fontSize: '0.8125rem', color: '#0f172a' }}>
                              {formatNumber(sigVal, 1)} / 100
                            </strong>
                          </div>
                        ))}
                      </div>
                    )}

                    {prio?.safety_override && (
                      <div style={{ marginTop: '12px', padding: '8px 12px', backgroundColor: '#fef2f2', border: '1px solid #fecaca', borderRadius: '6px', color: '#b91c1c', fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: '6px', fontWeight: 600 }}>
                        <ShieldAlert size={14} /> Immediate Safety Override: Physical hazard detected
                      </div>
                    )}
                  </div>

                </div>

                {/* Similar / Duplicate Issues Section */}
                <div style={{ backgroundColor: '#ffffff', borderRadius: '10px', border: '1px solid #e2e8f0', padding: '16px' }}>
                  <div style={{ fontSize: '0.875rem', fontWeight: 700, color: '#1e293b', marginBottom: '10px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <Copy size={18} color="#2563eb" /> Retrieved Similar &amp; Duplicate Issues (TF-IDF Cosine Retrieval)
                  </div>

                  {duplicates.length === 0 ? (
                    <p style={{ fontSize: '0.8125rem', color: '#64748b', fontStyle: 'italic' }}>
                      No closely matching duplicate complaints found in the indexed incident corpus.
                    </p>
                  ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                      {duplicates.map((dup, i) => {
                        const sim = Number(dup?.similarity_score) || 0;
                        const isHighMatch = sim >= 0.50 || dup?.similarity_level === 'HIGH';
                        return (
                          <div key={i} style={{
                            padding: '10px 14px',
                            borderRadius: '8px',
                            backgroundColor: isHighMatch ? '#fffbeb' : '#f8fafc',
                            border: isHighMatch ? '1px solid #fcd34d' : '1px solid #e2e8f0',
                            display: 'flex',
                            flexDirection: 'column',
                            gap: '4px',
                          }}>
                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                <span style={{ fontSize: '0.75rem', fontFamily: 'monospace', fontWeight: 700, color: '#475569' }}>
                                  {dup.candidate_id || dup.suggested_complaint_id || `Candidate #${i + 1}`}
                                </span>
                                {isHighMatch && (
                                  <span style={{ fontSize: '0.6875rem', fontWeight: 700, backgroundColor: '#f59e0b', color: '#ffffff', padding: '2px 6px', borderRadius: '4px' }}>
                                    Potential Duplicate
                                  </span>
                                )}
                              </div>
                              <span style={{ fontSize: '0.8125rem', fontWeight: 700, color: isHighMatch ? '#b45309' : '#475569' }}>
                                {formatPercent(sim)} Similarity
                              </span>
                            </div>
                            <p style={{ fontSize: '0.8125rem', color: '#334155', margin: 0, fontStyle: 'italic' }}>
                              &ldquo;{safeString(dup.candidate_text || dup.suggested_text)}&rdquo;
                            </p>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>

                {/* Priority Override & Audit Trail */}
                <div style={{ backgroundColor: '#ffffff', borderRadius: '10px', border: '1px solid #e2e8f0', padding: '16px' }}>
                  <div style={{ fontSize: '0.875rem', fontWeight: 700, color: '#1e293b', marginBottom: '10px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <UserCheck size={18} color="#2563eb" /> Priority Governance &amp; Override Audit Trail
                  </div>

                  {overrides.length > 0 ? (
                    <div style={{ marginBottom: '16px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                      {overrides.map((ovr) => (
                        <div key={ovr.id} style={{ padding: '8px 12px', backgroundColor: '#f1f5f9', borderRadius: '6px', fontSize: '0.8125rem' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', color: '#475569', marginBottom: '2px' }}>
                            <span><strong>{ovr.staff_username || `Staff #${ovr.staff_id}`}</strong> changed priority:</span>
                            <span style={{ fontSize: '0.75rem' }}>{formatDate(ovr.timestamp)}</span>
                          </div>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', margin: '4px 0' }}>
                            <span style={{ textTransform: 'uppercase', fontWeight: 700, color: '#64748b' }}>{ovr.original_priority}</span>
                            <ArrowRight size={14} color="#64748b" />
                            <span style={{ textTransform: 'uppercase', fontWeight: 700, color: '#2563eb' }}>{ovr.override_priority}</span>
                          </div>
                          <div style={{ color: '#334155', fontStyle: 'italic' }}>
                            Reason: &ldquo;{ovr.reason}&rdquo;
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p style={{ fontSize: '0.8125rem', color: '#64748b', marginBottom: '16px' }}>
                      No manual priority overrides recorded. Operating on AI automated priority.
                    </p>
                  )}

                  {/* Staff / Admin Controls */}
                  {isStaffOrAdmin ? (
                    <div style={{ backgroundColor: '#f8fafc', padding: '14px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
                      <div style={{ fontSize: '0.8125rem', fontWeight: 700, color: '#1e293b', marginBottom: '10px' }}>
                        Staff Triage Controls
                      </div>

                      {/* Status Dropdown */}
                      <div style={{ marginBottom: '14px', display: 'flex', alignItems: 'center', gap: '12px' }}>
                        <label style={{ fontSize: '0.8125rem', fontWeight: 600, color: '#475569', minWidth: '100px' }}>
                          Update Status:
                        </label>
                        <select
                          value={newStatus}
                          onChange={handleStatusChange}
                          disabled={updating}
                          style={{
                            padding: '6px 12px',
                            borderRadius: '6px',
                            border: '1px solid #cbd5e1',
                            fontSize: '0.875rem',
                            backgroundColor: '#ffffff',
                          }}
                        >
                          <option value="submitted">Submitted</option>
                          <option value="in_progress">In Progress</option>
                          <option value="resolved">Resolved</option>
                          <option value="rejected">Rejected</option>
                        </select>
                      </div>

                      {/* Override Form */}
                      <form onSubmit={handlePriorityOverride} style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                          <label style={{ fontSize: '0.8125rem', fontWeight: 600, color: '#475569', minWidth: '100px' }}>
                            Override Priority:
                          </label>
                          <select
                            value={overridePriority}
                            onChange={(e) => setOverridePriority(e.target.value)}
                            style={{
                              padding: '6px 12px',
                              borderRadius: '6px',
                              border: '1px solid #cbd5e1',
                              fontSize: '0.875rem',
                              backgroundColor: '#ffffff',
                            }}
                          >
                            <option value="LOW">Low</option>
                            <option value="MEDIUM">Medium</option>
                            <option value="HIGH">High</option>
                            <option value="CRITICAL">Critical</option>
                          </select>
                        </div>

                        <div>
                          <label style={{ fontSize: '0.8125rem', fontWeight: 600, color: '#475569', display: 'block', marginBottom: '4px' }}>
                            Mandatory Justification Reason:
                          </label>
                          <input
                            type="text"
                            placeholder="Explain why the automated priority is being overridden..."
                            value={overrideReason}
                            onChange={(e) => setOverrideReason(e.target.value)}
                            style={{
                              width: '100%',
                              padding: '8px 12px',
                              borderRadius: '6px',
                              border: '1px solid #cbd5e1',
                              fontSize: '0.875rem',
                            }}
                          />
                        </div>

                        <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '6px' }}>
                          <button
                            type="submit"
                            disabled={updating || !overrideReason.trim()}
                            style={{
                              backgroundColor: '#2563eb',
                              color: '#ffffff',
                              padding: '7px 16px',
                              borderRadius: '6px',
                              border: 'none',
                              fontWeight: 600,
                              fontSize: '0.8125rem',
                              cursor: updating || !overrideReason.trim() ? 'not-allowed' : 'pointer',
                              opacity: updating || !overrideReason.trim() ? 0.6 : 1,
                            }}
                          >
                            {updating ? 'Saving...' : 'Record Priority Override'}
                          </button>
                        </div>
                      </form>
                    </div>
                  ) : (
                    <div style={{ fontSize: '0.75rem', color: '#64748b', fontStyle: 'italic' }}>
                      Note: Only authorized department staff or administrators may adjust status or override priority.
                    </div>
                  )}
                </div>
              </>
            )}

          </div>

          {/* Modal Footer */}
          <div style={{
            padding: '12px 24px',
            borderTop: '1px solid #e2e8f0',
            display: 'flex',
            justifyContent: 'flex-end',
            backgroundColor: '#f8fafc',
          }}>
            <button
              onClick={onClose}
              style={{
                padding: '8px 20px',
                backgroundColor: '#e2e8f0',
                color: '#334155',
                border: 'none',
                borderRadius: '6px',
                fontWeight: 600,
                fontSize: '0.875rem',
                cursor: 'pointer',
              }}
            >
              Close
            </button>
          </div>

        </div>
      </div>
    </ErrorBoundary>
  );
}
