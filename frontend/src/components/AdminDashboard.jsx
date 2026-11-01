import React, { useState, useEffect } from 'react';
import { 
  BarChart3, AlertTriangle, CheckCircle, ShieldAlert, 
  MapPin, RefreshCw, Sparkles, Info
} from 'lucide-react';
import { apiGetAnalyticsOverview, apiGetRecurringClusters } from '../api';
import { formatNumber, formatPercent, safeArray, safeString } from '../utils/formatters';
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

export default function AdminDashboard() {
  const [overview, setOverview] = useState(null);
  const [clusters, setClusters] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const fetchAnalytics = async () => {
    setLoading(true);
    setError('');
    try {
      const [overviewData, clusterData] = await Promise.all([
        apiGetAnalyticsOverview(),
        apiGetRecurringClusters(),
      ]);
      setOverview(overviewData || null);
      setClusters(safeArray(clusterData));
    } catch (err) {
      console.error('Failed to load analytics:', err);
      setError(err.message || 'Failed to load analytics data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, []);

  if (loading && !overview) {
    return (
      <div style={{ maxWidth: '1280px', margin: '0 auto', padding: '48px 16px', textAlign: 'center', color: '#64748b' }}>
        <RefreshCw size={28} className="animate-spin" style={{ margin: '0 auto 12px auto' }} />
        <p>Loading administrative intelligence and clustering analytics...</p>
      </div>
    );
  }

  // Safe extraction of KPIs from top-level overview response or fallback
  const total = Number(overview?.total_complaints) || 0;
  const resolved = Number(overview?.resolved_count) || 0;
  const critical = Number(overview?.critical_high_count) || 0;
  const pendingReview = Number(overview?.pending_review_count) || 0;
  const inProgress = Number(overview?.in_progress_count) || 0;

  const resolutionRatePct = total > 0 ? (resolved / total) * 100 : 0;
  const reviewRatePct = total > 0 ? (pendingReview / total) * 100 : 0;

  // Normalize category distribution to array of primitive objects
  let categoryList = [];
  if (Array.isArray(overview?.category_distribution)) {
    categoryList = overview.category_distribution.map((item) => ({
      category: safeString(item?.category, 'Unknown'),
      category_name: safeString(item?.category_name || CATEGORY_NAMES[item?.category], item?.category || 'General'),
      count: Number(item?.count) || 0,
      percentage: Number(item?.percentage) || 0,
    }));
  } else if (overview?.category_distribution && typeof overview.category_distribution === 'object') {
    categoryList = Object.entries(overview.category_distribution).map(([code, countVal]) => {
      const cnt = typeof countVal === 'object' ? Number(countVal?.count) || 0 : Number(countVal) || 0;
      const pct = typeof countVal === 'object' ? Number(countVal?.percentage) || 0 : (total > 0 ? (cnt / total) * 100 : 0);
      return {
        category: code,
        category_name: CATEGORY_NAMES[code] || code,
        count: cnt,
        percentage: pct,
      };
    });
  }

  const maxCatCount = Math.max(...categoryList.map((c) => c.count), 1);
  const hotspots = safeArray(overview?.hotspots);
  const clusterList = safeArray(clusters);

  return (
    <div style={{ maxWidth: '1280px', margin: '0 auto', padding: '24px 16px' }}>
      
      {/* Title & Refresh */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <h2 style={{ fontSize: '1.375rem', fontWeight: 800, color: '#0f172a' }}>
            Administrative Analytics & Pattern Discovery
          </h2>
          <p style={{ fontSize: '0.875rem', color: '#64748b' }}>
            High-level operational KPIs, department volume distribution, spatiotemporal hotspots, and unsupervised recurring clusters.
          </p>
        </div>

        <button
          onClick={fetchAnalytics}
          disabled={loading}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            padding: '8px 16px',
            backgroundColor: '#ffffff',
            border: '1px solid #cbd5e1',
            borderRadius: '8px',
            fontSize: '0.8125rem',
            fontWeight: 600,
            color: '#334155',
            cursor: loading ? 'not-allowed' : 'pointer',
            boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
            opacity: loading ? 0.7 : 1,
          }}
        >
          <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          {loading ? 'Refreshing...' : 'Refresh Analytics'}
        </button>
      </div>

      {error && (
        <div style={{ padding: '12px 16px', backgroundColor: '#fef2f2', border: '1px solid #fecaca', borderRadius: '8px', color: '#b91c1c', fontSize: '0.875rem', marginBottom: '20px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <strong>Error loading analytics:</strong> {error}
          </div>
          <button
            onClick={fetchAnalytics}
            style={{ backgroundColor: '#b91c1c', color: '#fff', border: 'none', padding: '4px 10px', borderRadius: '4px', fontSize: '0.75rem', cursor: 'pointer' }}
          >
            Retry
          </button>
        </div>
      )}

      {/* Academic Methodology / Data Sufficiency Banner */}
      <div style={{
        padding: '14px 18px',
        backgroundColor: '#f8fafc',
        border: '1px solid #cbd5e1',
        borderLeft: '4px solid #2563eb',
        borderRadius: '8px',
        marginBottom: '24px',
        display: 'flex',
        alignItems: 'flex-start',
        gap: '12px',
      }}>
        <Info size={20} color="#2563eb" style={{ flexShrink: 0, marginTop: '2px' }} />
        <div style={{ fontSize: '0.8125rem', color: '#334155', lineHeight: 1.5 }}>
          <strong style={{ color: '#0f172a' }}>Academic Data Sufficiency &amp; Calibration Notice:</strong>
          {' '}
          {overview?.trend_warning ? (
            <span>{overview.trend_warning}</span>
          ) : (
            <span>
              In accordance with Phase 7 methodology, current metrics reflect the active incident database (N={total}).
              Longitudinal trend confidence requires continuous observation across temporal windows to distinguish genuine spikes from stochastic variations.
              Unsupervised clusters with size &lt; 3 support or weak silhouette carry explicit weak-support indicators.
            </span>
          )}
        </div>
      </div>

      {/* KPI Cards Grid */}
      <ErrorBoundary name="Executive KPIs">
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px', marginBottom: '24px' }}>
          
          <div style={{ backgroundColor: '#ffffff', padding: '18px', borderRadius: '10px', border: '1px solid #e2e8f0', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
            <div style={{ fontSize: '0.75rem', fontWeight: 600, color: '#64748b' }}>Total Registered Complaints</div>
            <div style={{ fontSize: '1.75rem', fontWeight: 800, color: '#0f172a', margin: '4px 0' }}>{total}</div>
            <div style={{ fontSize: '0.75rem', color: '#475569' }}>
              {inProgress} currently in progress
            </div>
          </div>

          <div style={{ backgroundColor: '#ffffff', padding: '18px', borderRadius: '10px', border: '1px solid #e2e8f0', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
            <div style={{ fontSize: '0.75rem', fontWeight: 600, color: '#15803d', display: 'flex', alignItems: 'center', gap: '4px' }}>
              <CheckCircle size={14} /> Resolution Rate
            </div>
            <div style={{ fontSize: '1.75rem', fontWeight: 800, color: '#15803d', margin: '4px 0' }}>
              {formatPercent(resolutionRatePct)}
            </div>
            <div style={{ fontSize: '0.75rem', color: '#475569' }}>
              {resolved} of {total} marked resolved
            </div>
          </div>

          <div style={{ backgroundColor: '#ffffff', padding: '18px', borderRadius: '10px', border: '1px solid #e2e8f0', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
            <div style={{ fontSize: '0.75rem', fontWeight: 600, color: '#b91c1c', display: 'flex', alignItems: 'center', gap: '4px' }}>
              <ShieldAlert size={14} /> Critical / High Priority
            </div>
            <div style={{ fontSize: '1.75rem', fontWeight: 800, color: '#b91c1c', margin: '4px 0' }}>
              {critical}
            </div>
            <div style={{ fontSize: '0.75rem', color: '#475569' }}>Requiring expedited response</div>
          </div>

          <div style={{ backgroundColor: '#ffffff', padding: '18px', borderRadius: '10px', border: '1px solid #e2e8f0', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
            <div style={{ fontSize: '0.75rem', fontWeight: 600, color: '#b45309', display: 'flex', alignItems: 'center', gap: '4px' }}>
              <AlertTriangle size={14} /> Low-Confidence Triage Rate
            </div>
            <div style={{ fontSize: '1.75rem', fontWeight: 800, color: '#b45309', margin: '4px 0' }}>
              {formatPercent(reviewRatePct)}
            </div>
            <div style={{ fontSize: '0.75rem', color: '#475569' }}>
              {pendingReview} tickets flagged for staff review
            </div>
          </div>

        </div>
      </ErrorBoundary>

      {/* Main Analysis Section (2 Columns) */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(460px, 1fr))', gap: '24px', marginBottom: '24px' }}>
        
        {/* Category Distribution Chart */}
        <ErrorBoundary name="Category Distribution Chart">
          <div style={{ backgroundColor: '#ffffff', borderRadius: '12px', border: '1px solid #e2e8f0', padding: '20px', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
            <div style={{ fontSize: '1rem', fontWeight: 700, color: '#0f172a', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <BarChart3 size={18} color="#2563eb" /> Category Volume Distribution
            </div>
            <p style={{ fontSize: '0.75rem', color: '#64748b', marginBottom: '16px' }}>
              Class distribution of active and logged complaints across the 11 schema categories.
            </p>

            {categoryList.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '36px', color: '#94a3b8', fontSize: '0.875rem' }}>
                No category data available yet.
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {categoryList.map((item) => {
                  const pctWidth = Math.min(100, Math.max(2, (item.count / maxCatCount) * 100));
                  return (
                    <div key={item.category}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', marginBottom: '3px' }}>
                        <span style={{ fontWeight: 600, color: '#334155' }}>
                          {item.category} &bull; {item.category_name}
                        </span>
                        <span style={{ fontWeight: 700, color: '#0f172a' }}>
                          {item.count} {item.count === 1 ? 'ticket' : 'tickets'} ({formatPercent(item.percentage)})
                        </span>
                      </div>
                      <div style={{ height: '8px', width: '100%', backgroundColor: '#f1f5f9', borderRadius: '4px', overflow: 'hidden' }}>
                        <div style={{
                          height: '100%',
                          width: `${pctWidth.toFixed(0)}%`,
                          backgroundColor: '#2563eb',
                          borderRadius: '4px',
                        }} />
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </ErrorBoundary>

        {/* Spatiotemporal Hotspots Table */}
        <ErrorBoundary name="Spatiotemporal Hotspots">
          <div style={{ backgroundColor: '#ffffff', borderRadius: '12px', border: '1px solid #e2e8f0', padding: '20px', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
            <div style={{ fontSize: '1rem', fontWeight: 700, color: '#0f172a', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <MapPin size={18} color="#2563eb" /> Spatiotemporal Incident Hotspots
            </div>
            <p style={{ fontSize: '0.75rem', color: '#64748b', marginBottom: '16px' }}>
              Locations exhibiting recurring issues or multiple incident reports.
            </p>

            {hotspots.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '36px', color: '#94a3b8', fontSize: '0.875rem' }}>
                No multi-complaint spatial hotspots identified yet.
              </div>
            ) : (
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.8125rem' }}>
                  <thead>
                    <tr style={{ borderBottom: '2px solid #e2e8f0', color: '#475569', fontSize: '0.6875rem', textTransform: 'uppercase' }}>
                      <th style={{ padding: '8px 10px' }}>Location</th>
                      <th style={{ padding: '8px 10px' }}>Category</th>
                      <th style={{ padding: '8px 10px' }}>Count</th>
                      <th style={{ padding: '8px 10px' }}>Proportion</th>
                    </tr>
                  </thead>
                  <tbody>
                    {hotspots.map((h, idx) => {
                      const count = Number(h?.count || h?.complaint_count) || 0;
                      return (
                        <tr key={idx} style={{ borderBottom: '1px solid #f1f5f9' }}>
                          <td style={{ padding: '10px', fontWeight: 700, color: '#0f172a' }}>
                            {safeString(h?.location, 'General Campus')}
                          </td>
                          <td style={{ padding: '10px', color: '#475569' }}>
                            {safeString(h?.category_name || h?.category, 'General')}
                          </td>
                          <td style={{ padding: '10px' }}>
                            <span style={{
                              backgroundColor: count >= 3 ? '#fee2e2' : '#fef3c7',
                              color: count >= 3 ? '#b91c1c' : '#b45309',
                              fontWeight: 700,
                              fontSize: '0.75rem',
                              padding: '2px 8px',
                              borderRadius: '9999px',
                            }}>
                              {count} {count === 1 ? 'report' : 'reports'}
                            </span>
                          </td>
                          <td style={{ padding: '10px', color: '#64748b', fontSize: '0.75rem' }}>
                            {formatPercent(h?.percentage)}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </ErrorBoundary>

      </div>

      {/* Unsupervised Recurring-Issue Clusters (Phase 7 Integration) */}
      <ErrorBoundary name="Unsupervised Semantic Clusters">
        <div style={{ backgroundColor: '#ffffff', borderRadius: '12px', border: '1px solid #e2e8f0', padding: '20px', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px', flexWrap: 'wrap', gap: '8px' }}>
            <div style={{ fontSize: '1.0625rem', fontWeight: 700, color: '#0f172a', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Sparkles size={18} color="#2563eb" /> Discovered Recurring-Issue Clusters (Unsupervised Semantic Clustering)
            </div>
            <span style={{ fontSize: '0.75rem', color: '#64748b', backgroundColor: '#f1f5f9', padding: '3px 8px', borderRadius: '6px' }}>
              Method: TF-IDF + Spherical K-Means
            </span>
          </div>
          <p style={{ fontSize: '0.8125rem', color: '#64748b', marginBottom: '18px' }}>
            Automatically groups semantically related complaints across tickets, extracting characteristic keywords and representative incident descriptions.
          </p>

          {clusterList.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '36px', color: '#64748b', fontSize: '0.875rem' }}>
              <Sparkles size={28} style={{ margin: '0 auto 8px auto', opacity: 0.5, color: '#2563eb' }} />
              <p style={{ fontWeight: 600, color: '#1e293b' }}>Insufficient live data for clustering</p>
              <p style={{ fontSize: '0.8125rem', marginTop: '4px' }}>
                Unsupervised recurring clusters require at least 3 live complaints to extract semantic themes. As issues are reported, clusters will appear here automatically without synthetic fallbacks.
              </p>
            </div>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '16px' }}>
              {clusterList.map((cl, idx) => {
                const clusterId = cl.cluster_id !== undefined ? cl.cluster_id : idx;
                const size = Number(cl.size ?? cl.complaint_count) || 0;
                const isWeak = Boolean(cl.is_weakly_supported ?? cl.weak_cluster ?? (size < 3));
                const terms = safeArray(cl.top_terms || cl.top_keywords);
                const samples = safeArray(cl.representative_complaints || cl.sample_complaints);

                return (
                  <div key={clusterId} style={{
                    padding: '16px',
                    borderRadius: '10px',
                    border: isWeak ? '1px solid #fed7aa' : '1px solid #e2e8f0',
                    backgroundColor: isWeak ? '#fffaf5' : '#ffffff',
                    boxShadow: '0 1px 2px rgba(0,0,0,0.04)',
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                      <span style={{ fontSize: '0.875rem', fontWeight: 700, color: '#0f172a' }}>
                        {safeString(cl.label, `Cluster #${clusterId}`)}
                      </span>
                      <span style={{
                        fontSize: '0.75rem',
                        fontWeight: 700,
                        backgroundColor: '#eff6ff',
                        color: '#1d4ed8',
                        padding: '2px 8px',
                        borderRadius: '9999px',
                      }}>
                        {size} {size === 1 ? 'complaint' : 'complaints'}
                      </span>
                    </div>

                    {isWeak && (
                      <div style={{
                        fontSize: '0.6875rem',
                        fontWeight: 600,
                        color: '#c2410c',
                        backgroundColor: '#ffedd5',
                        padding: '3px 6px',
                        borderRadius: '4px',
                        marginBottom: '8px',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '4px',
                      }}>
                        <AlertTriangle size={11} /> Weak Support Cluster (Low sample density / exploratory)
                      </div>
                    )}

                    {/* Keywords */}
                    {terms.length > 0 && (
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', marginBottom: '10px' }}>
                        {terms.map((kw, i) => (
                          <span key={i} style={{
                            fontSize: '0.6875rem',
                            backgroundColor: '#f1f5f9',
                            color: '#475569',
                            padding: '2px 6px',
                            borderRadius: '4px',
                            fontFamily: 'monospace',
                          }}>
                            {safeString(kw)}
                          </span>
                        ))}
                      </div>
                    )}

                    {/* Representative Sample */}
                    {samples.length > 0 && (
                      <div style={{
                        fontSize: '0.75rem',
                        color: '#334155',
                        backgroundColor: '#f8fafc',
                        padding: '8px 10px',
                        borderRadius: '6px',
                        borderLeft: '3px solid #2563eb',
                        fontStyle: 'italic',
                      }}>
                        &ldquo;{safeString(samples[0])}&rdquo;
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </ErrorBoundary>

    </div>
  );
}
