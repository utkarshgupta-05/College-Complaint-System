import React, { useState, useEffect, useRef } from 'react';
import { 
  Send, Sparkles, AlertTriangle, CheckCircle, Clock, 
  MapPin, ShieldAlert, FileText, ChevronRight, Layers, RefreshCw
} from 'lucide-react';
import { apiAnalyzeComplaint, apiSubmitComplaint, apiListComplaints } from '../api';
import { 
  formatNumber, formatPercent, safeArray, safeString, 
  safeObject, normalizePriority, normalizeStatus, formatDate 
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

export default function StudentPortal({ currentUser }) {
  const [activeTab, setActiveTab] = useState('submit'); // 'submit' | 'history'
  const [complaintText, setComplaintText] = useState('');
  const [location, setLocation] = useState('');
  const [department, setDepartment] = useState(currentUser?.department || 'Computer Science');
  
  // Real-time AI preview state
  const [analysis, setAnalysis] = useState(null);
  const [analysisError, setAnalysisError] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const debounceTimerRef = useRef(null);
  const activeRequestIdRef = useRef(0);
  const abortControllerRef = useRef(null);

  // Submission state
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState('');
  const [lastSubmittedId, setLastSubmittedId] = useState(null);

  // Complaints history state
  const [myComplaints, setMyComplaints] = useState([]);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [selectedComplaintId, setSelectedComplaintId] = useState(null);

  // Debounced real-time analysis effect with race-condition prevention & cancellation
  useEffect(() => {
    // Clear any previous debounce timeout
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }

    const trimmedText = complaintText.trim();
    const trimmedLocation = location.trim();

    // Incomplete or short complaints (< 10 chars) do not trigger API requests
    if (trimmedText.length < 10) {
      activeRequestIdRef.current++; // Invalidate any pending in-flight response
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      setAnalysis(null);
      setAnalysisError('');
      setIsAnalyzing(false);
      return;
    }

    setIsAnalyzing(true);
    setAnalysisError('');

    const requestId = ++activeRequestIdRef.current;

    debounceTimerRef.current = setTimeout(async () => {
      // Abort prior in-flight request
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      abortControllerRef.current = new AbortController();

      try {
        const result = await apiAnalyzeComplaint(trimmedText, trimmedLocation, {
          signal: abortControllerRef.current.signal,
        });

        // Only commit result if this is still the active request
        if (requestId === activeRequestIdRef.current) {
          setAnalysis(result);
          setAnalysisError('');
        }
      } catch (err) {
        if (err.name === 'AbortError') {
          // Normal abort from typing, do not flag as error
          return;
        }
        if (requestId === activeRequestIdRef.current) {
          console.warn('Real-time AI triage preview failed:', err.message);
          setAnalysisError(err.message || 'Could not fetch live triage preview');
        }
      } finally {
        if (requestId === activeRequestIdRef.current) {
          setIsAnalyzing(false);
        }
      }
    }, 450);

    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, [complaintText, location]);

  // Load complaints
  const fetchComplaints = async () => {
    setLoadingHistory(true);
    try {
      const data = await apiListComplaints();
      setMyComplaints(safeArray(data));
    } catch (err) {
      console.error('Failed to fetch complaints:', err);
    } finally {
      setLoadingHistory(false);
    }
  };

  useEffect(() => {
    fetchComplaints();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!complaintText.trim() || complaintText.trim().length < 10) {
      setSubmitError('Complaint text must be at least 10 characters long.');
      return;
    }
    setSubmitting(true);
    setSubmitError('');
    try {
      const newComplaint = await apiSubmitComplaint(
        complaintText.trim(),
        location.trim() || undefined,
        department.trim() || undefined
      );
      setLastSubmittedId(newComplaint.id);
      setComplaintText('');
      setLocation('');
      setAnalysis(null);
      fetchComplaints();
    } catch (err) {
      setSubmitError(err.message || 'Failed to submit complaint.');
    } finally {
      setSubmitting(false);
    }
  };

  // Safely extract AI preview fields
  const pred = analysis?.prediction || null;
  const prio = analysis?.priority || null;
  const duplicates = safeArray(analysis?.duplicate_suggestions || analysis?.duplicates);

  const predictedCategoryCode = pred?.predicted_category || '';
  const predictedCategoryName = safeString(
    pred?.category_name || CATEGORY_NAMES[predictedCategoryCode],
    predictedCategoryCode ? `Category ${predictedCategoryCode}` : 'Evaluating...'
  );
  const confidenceVal = pred?.confidence !== undefined ? pred.confidence : pred?.confidence_score;
  const needsReview = Boolean(pred?.needs_human_review || pred?.needs_review || pred?.low_confidence);

  const priorityScoreVal = prio?.score !== undefined ? prio.score : prio?.priority_score;
  const priorityLevelKey = normalizePriority(prio?.final_priority || prio?.priority_level || prio?.suggested_priority);
  const priorityStyle = PRIORITY_COLORS[priorityLevelKey] || PRIORITY_COLORS.medium;
  const isSafetyOverridden = Boolean(prio?.safety_override || prio?.safety_flag || prio?.escalation_recommended);
  const signals = safeObject(prio?.signals || prio?.factors);

  return (
    <ErrorBoundary name="Student Portal">
      <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '24px 16px' }}>
        
        {/* Tab Navigation */}
        <div style={{ display: 'flex', gap: '8px', borderBottom: '1px solid #e2e8f0', marginBottom: '24px' }}>
          <button
            onClick={() => setActiveTab('submit')}
            style={{
              padding: '10px 18px',
              border: 'none',
              borderBottom: activeTab === 'submit' ? '3px solid #2563eb' : '3px solid transparent',
              background: 'none',
              fontWeight: 700,
              fontSize: '0.9375rem',
              color: activeTab === 'submit' ? '#2563eb' : '#64748b',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
            }}
          >
            <Send size={16} /> Submit New Complaint
          </button>

          <button
            onClick={() => {
              setActiveTab('history');
              fetchComplaints();
            }}
            style={{
              padding: '10px 18px',
              border: 'none',
              borderBottom: activeTab === 'history' ? '3px solid #2563eb' : '3px solid transparent',
              background: 'none',
              fontWeight: 700,
              fontSize: '0.9375rem',
              color: activeTab === 'history' ? '#2563eb' : '#64748b',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
            }}
          >
            <Clock size={16} /> My Submitted Complaints ({myComplaints.length})
          </button>
        </div>

        {/* Tab 1: Submission Form */}
        {activeTab === 'submit' && (
          <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1.2fr) minmax(0, 0.8fr)', gap: '24px' }}>
            
            {/* Left: Input Form */}
            <div style={{ backgroundColor: '#ffffff', borderRadius: '12px', border: '1px solid #e2e8f0', padding: '24px', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
              <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#0f172a', marginBottom: '6px' }}>
                Submit a Campus Incident or Issue
              </h2>
              <p style={{ fontSize: '0.875rem', color: '#64748b', marginBottom: '20px' }}>
                Describe the problem clearly. The integrated AI models evaluate category routing, safety priority, and duplicate tickets in real time.
              </p>

              {lastSubmittedId && (
                <div style={{
                  padding: '14px 18px',
                  backgroundColor: '#f0fdf4',
                  border: '1px solid #bbf7d0',
                  borderRadius: '8px',
                  color: '#166534',
                  marginBottom: '20px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <CheckCircle size={18} />
                    <span>
                      Complaint submitted successfully as <strong>{lastSubmittedId}</strong>!
                    </span>
                  </div>
                  <button
                    onClick={() => setSelectedComplaintId(lastSubmittedId)}
                    style={{
                      backgroundColor: '#166534',
                      color: '#ffffff',
                      border: 'none',
                      borderRadius: '6px',
                      padding: '4px 10px',
                      fontSize: '0.75rem',
                      fontWeight: 600,
                      cursor: 'pointer',
                    }}
                  >
                    View Ticket
                  </button>
                </div>
              )}

              {submitError && (
                <div style={{
                  padding: '12px 16px',
                  backgroundColor: '#fef2f2',
                  border: '1px solid #fecaca',
                  borderRadius: '8px',
                  color: '#b91c1c',
                  fontSize: '0.875rem',
                  marginBottom: '20px',
                }}>
                  <strong>Error:</strong> {submitError}
                </div>
              )}

              <form onSubmit={handleSubmit}>
                
                {/* Complaint Textarea */}
                <div style={{ marginBottom: '16px' }}>
                  <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 600, color: '#334155', marginBottom: '6px' }}>
                    Complaint Description *
                  </label>
                  <textarea
                    rows={5}
                    value={complaintText}
                    onChange={(e) => setComplaintText(e.target.value)}
                    placeholder="e.g. In Hostel Block B Room 204, water has been leaking from the ceiling since yesterday, posing an electrical hazard near the fan switch..."
                    style={{
                      width: '100%',
                      padding: '12px',
                      borderRadius: '8px',
                      border: '1px solid #cbd5e1',
                      fontSize: '0.9375rem',
                      lineHeight: 1.5,
                      resize: 'vertical',
                    }}
                  />
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: '#64748b', marginTop: '4px' }}>
                    <span>Min. 10 characters</span>
                    <span>{complaintText.length} characters</span>
                  </div>
                </div>

                {/* Location and Department */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '20px' }}>
                  <div>
                    <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 600, color: '#334155', marginBottom: '6px' }}>
                      Specific Location
                    </label>
                    <input
                      type="text"
                      value={location}
                      onChange={(e) => setLocation(e.target.value)}
                      placeholder="e.g. Hostel B Room 204 / Library"
                      style={{
                        width: '100%',
                        padding: '10px 12px',
                        borderRadius: '8px',
                        border: '1px solid #cbd5e1',
                        fontSize: '0.875rem',
                      }}
                    />
                  </div>

                  <div>
                    <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 600, color: '#334155', marginBottom: '6px' }}>
                      Student Department
                    </label>
                    <select
                      value={department}
                      onChange={(e) => setDepartment(e.target.value)}
                      style={{
                        width: '100%',
                        padding: '10px 12px',
                        borderRadius: '8px',
                        border: '1px solid #cbd5e1',
                        fontSize: '0.875rem',
                        backgroundColor: '#ffffff',
                      }}
                    >
                      <option value="Computer Science">Computer Science</option>
                      <option value="Mechanical Engineering">Mechanical Engineering</option>
                      <option value="Electrical Engineering">Electrical Engineering</option>
                      <option value="Civil Engineering">Civil Engineering</option>
                      <option value="Information Technology">Information Technology</option>
                      <option value="Business Administration">Business Administration</option>
                    </select>
                  </div>
                </div>

                {/* Submit Button */}
                <button
                  type="submit"
                  disabled={submitting || complaintText.trim().length < 10}
                  style={{
                    width: '100%',
                    padding: '12px 20px',
                    backgroundColor: '#2563eb',
                    color: '#ffffff',
                    border: 'none',
                    borderRadius: '8px',
                    fontWeight: 700,
                    fontSize: '0.9375rem',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '8px',
                    opacity: submitting || complaintText.trim().length < 10 ? 0.6 : 1,
                    cursor: submitting || complaintText.trim().length < 10 ? 'not-allowed' : 'pointer',
                  }}
                >
                  <Send size={18} />
                  {submitting ? 'Submitting & Routing...' : 'Submit Incident Ticket'}
                </button>
              </form>
            </div>

            {/* Right: Real-Time AI Triage Preview */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div style={{
                backgroundColor: '#ffffff',
                borderRadius: '12px',
                border: '1px solid #e2e8f0',
                padding: '20px',
                boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 700, fontSize: '0.9375rem', color: '#1e293b' }}>
                    <Sparkles size={18} color="#2563eb" /> AI Pre-Triage Assistant
                  </div>
                  {isAnalyzing && (
                    <span style={{ fontSize: '0.75rem', color: '#2563eb', display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <RefreshCw size={12} className="animate-spin" /> Evaluating...
                    </span>
                  )}
                </div>

                {analysisError && (
                  <div style={{ padding: '8px 12px', backgroundColor: '#fffbeb', border: '1px solid #fef3c7', borderRadius: '6px', color: '#92400e', fontSize: '0.75rem', marginBottom: '12px' }}>
                    Note: Live triage preview temporarily unavailable ({analysisError}).
                  </div>
                )}

                {!analysis ? (
                  <div style={{ textAlign: 'center', padding: '36px 16px', color: '#94a3b8' }}>
                    <Layers size={36} style={{ margin: '0 auto 12px auto', opacity: 0.5 }} />
                    <p style={{ fontSize: '0.875rem' }}>
                      Type your complaint on the left (at least 10 characters) to see real-time automated department routing, priority calculation, and duplicate detection.
                    </p>
                  </div>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                    
                    {/* Category Routing Preview */}
                    <div style={{ padding: '12px', backgroundColor: '#f8fafc', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
                      <div style={{ fontSize: '0.75rem', color: '#64748b' }}>Predicted Category</div>
                      <div style={{ fontSize: '1rem', fontWeight: 700, color: '#0f172a', margin: '2px 0 6px 0' }}>
                        {predictedCategoryCode ? `${predictedCategoryCode}: ` : ''}{predictedCategoryName}
                      </div>
                      
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: '#475569', marginBottom: '4px' }}>
                        <span>Model Confidence:</span>
                        <strong>{formatPercent(confidenceVal)}</strong>
                      </div>

                      <div style={{ height: '6px', width: '100%', backgroundColor: '#e2e8f0', borderRadius: '3px', overflow: 'hidden' }}>
                        <div style={{
                          height: '100%',
                          width: formatPercent(confidenceVal),
                          backgroundColor: needsReview ? '#f59e0b' : '#2563eb',
                          borderRadius: '3px',
                        }} />
                      </div>

                      {needsReview && (
                        <div style={{ marginTop: '6px', fontSize: '0.75rem', color: '#b45309', display: 'flex', alignItems: 'center', gap: '4px' }}>
                          <AlertTriangle size={12} /> Low confidence: Ticket will be flagged for staff review
                        </div>
                      )}
                    </div>

                    {/* Priority Scoring Preview */}
                    <div style={{ padding: '12px', backgroundColor: '#f8fafc', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                        <div style={{ fontSize: '0.75rem', color: '#64748b' }}>Calculated Priority</div>
                        <span style={{
                          fontSize: '0.75rem',
                          fontWeight: 700,
                          textTransform: 'uppercase',
                          padding: '2px 8px',
                          borderRadius: '9999px',
                          backgroundColor: priorityStyle.bg,
                          color: priorityStyle.text,
                          border: `1px solid ${priorityStyle.border}`,
                        }}>
                          {priorityLevelKey} ({formatNumber(priorityScoreVal, 1)}/100)
                        </span>
                      </div>

                      {Object.keys(signals).length > 0 && (
                        <div style={{ fontSize: '0.75rem', color: '#475569' }}>
                          Severity: {formatNumber(signals.severity_language ?? signals.base_severity, 0)} &bull; 
                          Safety Match: {formatNumber(signals.safety_keyword_match ?? signals.urgency_score, 0)} &bull; 
                          Recurrence: {formatNumber(signals.recurrence_score ?? signals.repeat_factor, 0)}
                        </div>
                      )}

                      {isSafetyOverridden && (
                        <div style={{ marginTop: '8px', padding: '6px 8px', backgroundColor: '#fef2f2', border: '1px solid #fecaca', borderRadius: '4px', color: '#b91c1c', fontSize: '0.75rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '4px' }}>
                          <ShieldAlert size={12} /> Safety Alert: Critical override triggered
                        </div>
                      )}
                    </div>

                    {/* Duplicate Issue Alert */}
                    {duplicates.length > 0 && (
                      <div style={{
                        padding: '12px',
                        backgroundColor: '#fffbeb',
                        borderRadius: '8px',
                        border: '1px solid #fcd34d',
                      }}>
                        <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#b45309', display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '4px' }}>
                          <AlertTriangle size={14} /> Potential Existing Match Detected
                        </div>
                        <p style={{ fontSize: '0.8125rem', color: '#92400e', margin: '4px 0' }}>
                          Found similar ticket ({formatPercent(duplicates[0]?.similarity_score)} match):
                        </p>
                        <div style={{ fontSize: '0.75rem', color: '#78350f', fontStyle: 'italic', backgroundColor: 'rgba(255,255,255,0.6)', padding: '6px 8px', borderRadius: '4px' }}>
                          &ldquo;{safeString(duplicates[0]?.candidate_text || duplicates[0]?.suggested_text)}&rdquo;
                        </div>
                      </div>
                    )}

                  </div>
                )}
              </div>
            </div>

          </div>
        )}

        {/* Tab 2: Complaints History */}
        {activeTab === 'history' && (
          <div style={{ backgroundColor: '#ffffff', borderRadius: '12px', border: '1px solid #e2e8f0', padding: '20px', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h3 style={{ fontSize: '1.125rem', fontWeight: 700, color: '#0f172a' }}>
                Your Registered Complaints ({myComplaints.length})
              </h3>
              <button
                onClick={fetchComplaints}
                disabled={loadingHistory}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '6px 12px',
                  backgroundColor: '#f1f5f9',
                  color: '#334155',
                  border: 'none',
                  borderRadius: '6px',
                  fontSize: '0.8125rem',
                  fontWeight: 600,
                  cursor: loadingHistory ? 'not-allowed' : 'pointer',
                }}
              >
                <RefreshCw size={14} className={loadingHistory ? 'animate-spin' : ''} /> Refresh
              </button>
            </div>

            {loadingHistory ? (
              <div style={{ textAlign: 'center', padding: '40px', color: '#64748b' }}>
                Loading submitted complaints...
              </div>
            ) : myComplaints.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '48px 16px', color: '#94a3b8' }}>
                <FileText size={40} style={{ margin: '0 auto 12px auto', opacity: 0.5 }} />
                <p style={{ fontSize: '0.9375rem', fontWeight: 500 }}>No complaints submitted yet.</p>
                <p style={{ fontSize: '0.8125rem' }}>Switch to the 'Submit New Complaint' tab to lodge your first issue.</p>
              </div>
            ) : (
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.875rem' }}>
                  <thead>
                    <tr style={{ borderBottom: '2px solid #e2e8f0', color: '#475569', fontSize: '0.75rem', textTransform: 'uppercase' }}>
                      <th style={{ padding: '10px 12px' }}>Ticket ID</th>
                      <th style={{ padding: '10px 12px' }}>Description</th>
                      <th style={{ padding: '10px 12px' }}>Location</th>
                      <th style={{ padding: '10px 12px' }}>Category</th>
                      <th style={{ padding: '10px 12px' }}>Priority</th>
                      <th style={{ padding: '10px 12px' }}>Status</th>
                      <th style={{ padding: '10px 12px', textAlign: 'right' }}>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {myComplaints.map((c) => {
                      const prioKey = normalizePriority(c?.final_priority || c?.priority?.effective_priority);
                      const prioSt = PRIORITY_COLORS[prioKey] || PRIORITY_COLORS.medium;
                      const statKey = normalizeStatus(c?.status);
                      const statSt = STATUS_COLORS[statKey] || STATUS_COLORS.submitted;
                      const catDisplay = safeString(c?.category_name || c?.predicted_category, '—');

                      return (
                        <tr key={c.id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                          <td style={{ padding: '12px', fontFamily: 'monospace', fontWeight: 700, color: '#1e293b' }}>
                            {c.id}
                          </td>
                          <td style={{ padding: '12px', maxWidth: '300px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                            {c.complaint_text}
                          </td>
                          <td style={{ padding: '12px', color: '#64748b' }}>
                            {safeString(c.location)}
                          </td>
                          <td style={{ padding: '12px' }}>
                            <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#334155' }}>
                              {catDisplay}
                            </span>
                          </td>
                          <td style={{ padding: '12px' }}>
                            <span style={{
                              fontSize: '0.75rem',
                              fontWeight: 700,
                              textTransform: 'uppercase',
                              padding: '2px 8px',
                              borderRadius: '9999px',
                              backgroundColor: prioSt.bg,
                              color: prioSt.text,
                              border: `1px solid ${prioSt.border}`,
                            }}>
                              {prioKey}
                            </span>
                          </td>
                          <td style={{ padding: '12px' }}>
                            <span style={{
                              fontSize: '0.75rem',
                              fontWeight: 700,
                              textTransform: 'uppercase',
                              padding: '2px 8px',
                              borderRadius: '9999px',
                              backgroundColor: statSt.bg,
                              color: statSt.text,
                            }}>
                              {statKey.replace('_', ' ')}
                            </span>
                          </td>
                          <td style={{ padding: '12px', textAlign: 'right' }}>
                            <button
                              onClick={() => setSelectedComplaintId(c.id)}
                              style={{
                                backgroundColor: '#f1f5f9',
                                color: '#2563eb',
                                border: 'none',
                                padding: '6px 12px',
                                borderRadius: '6px',
                                fontSize: '0.75rem',
                                fontWeight: 600,
                                cursor: 'pointer',
                              }}
                            >
                              Details
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
        )}

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
