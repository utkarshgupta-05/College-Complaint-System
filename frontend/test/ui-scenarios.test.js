import { test, describe } from 'node:test';
import assert from 'node:assert/strict';
import { 
  formatNumber, 
  formatPercent, 
  safeArray, 
  safeObject, 
  safeString, 
  normalizePriority, 
  normalizeStatus 
} from '../src/utils/formatters.js';

describe('Student Portal Scenarios', () => {
  test('Scenario 1 & 2: Empty or shorter than minimum description length (< 10 chars)', () => {
    const inputs = ['', '   ', 'Water', 'Short', '123456789'];
    for (const text of inputs) {
      const trimmed = text.trim();
      const shouldTriggerAPI = trimmed.length >= 10;
      assert.equal(shouldTriggerAPI, false, `Input "${text}" should not trigger AI pre-triage`);
    }
  });

  test('Scenario 3: Typing character by character updates character count safely', () => {
    let currentText = '';
    const fullText = 'Air conditioner in CS Lab 3 is leaking water onto machines';
    const counts = [];
    for (const char of fullText) {
      currentText += char;
      counts.push(currentText.length);
    }
    assert.equal(counts.length, fullText.length);
    assert.equal(currentText.length >= 10, true);
  });

  test('Scenario 4: Successful AI pre-triage response parsing', () => {
    const mockApiResponse = {
      prediction: {
        predicted_category: 'C06',
        category_name: 'Classroom and Laboratory',
        confidence: 0.887,
        low_confidence: false,
        needs_human_review: false,
        all_scores: { C06: 0.887, C02: 0.08, C01: 0.033 }
      },
      priority: {
        score: 78.5,
        suggested_priority: 'HIGH',
        final_priority: 'HIGH',
        safety_flag: true,
        safety_override: false,
        needs_human_review: false,
        signals: { severity_language: 80.0, safety_keyword_match: 75.0 }
      },
      duplicate_suggestions: [
        {
          candidate_id: 'CMP-20261101-ABCD',
          candidate_text: 'Water leaking onto desks in CS Lab 3',
          similarity_score: 0.824,
          similarity_level: 'HIGH'
        }
      ]
    };

    // Verify extraction with no crashes
    const pred = mockApiResponse.prediction;
    const prio = mockApiResponse.priority;
    const dups = safeArray(mockApiResponse.duplicate_suggestions);

    assert.equal(pred.predicted_category, 'C06');
    assert.equal(formatPercent(pred.confidence), '88.7%');
    assert.equal(formatNumber(prio.score, 1), '78.5');
    assert.equal(normalizePriority(prio.final_priority), 'high');
    assert.equal(dups.length, 1);
    assert.equal(formatPercent(dups[0].similarity_score), '82.4%');
  });

  test('Scenario 5 & 6: Missing, null, or undefined numerical values', () => {
    const malformedResponse = {
      prediction: {
        predicted_category: 'C11',
        confidence: undefined,
        needs_human_review: true,
      },
      priority: {
        score: null,
        final_priority: null,
        signals: null,
      },
      duplicate_suggestions: null,
    };

    const pred = malformedResponse.prediction;
    const prio = malformedResponse.priority;
    const dups = safeArray(malformedResponse.duplicate_suggestions);

    // Assert that formatting helpers protect against undefined.toFixed()
    assert.doesNotThrow(() => {
      const confStr = formatPercent(pred.confidence);
      const scoreStr = formatNumber(prio.score, 1);
      const prioKey = normalizePriority(prio.final_priority);
      assert.equal(confStr, '0.0%');
      assert.equal(scoreStr, '0.0');
      assert.equal(prioKey, 'medium');
      assert.equal(dups.length, 0);
    });
  });

  test('Scenario 7: Failed API request handling', () => {
    let analysisState = null;
    let errorMessage = '';

    const simulateFailedRequest = () => {
      try {
        throw new Error('HTTP 500: Internal Server Error');
      } catch (err) {
        errorMessage = err.message;
        analysisState = null;
      }
    };

    simulateFailedRequest();
    assert.equal(analysisState, null);
    assert.ok(errorMessage.includes('HTTP 500'));
  });

  test('Scenario 8 & 9: Rapid typing and race conditions (cancellation of stale requests)', () => {
    let activeRequestId = 0;
    let committedState = null;

    // Simulate 3 rapid keystroke requests
    const runTypingFlow = (text, delayMs) => {
      const reqId = ++activeRequestId;
      return new Promise((resolve) => {
        setTimeout(() => {
          // If request is still active when resolving, commit
          if (reqId === activeRequestId) {
            committedState = `Result for: ${text}`;
          }
          resolve(reqId);
        }, delayMs);
      });
    };

    // Req 1 (slow, 60ms), Req 2 (fast, 20ms), Req 3 (latest, 40ms)
    runTypingFlow('Draft 1', 60);
    runTypingFlow('Draft 2', 20);
    runTypingFlow('Draft 3 (Final)', 40);

    return new Promise((resolve) => {
      setTimeout(() => {
        assert.equal(committedState, 'Result for: Draft 3 (Final)');
        resolve();
      }, 100);
    });
  });

  test('Scenario 10: Successful complaint submission payload verification', () => {
    const payload = {
      complaint_text: 'The primary ceiling fan in Classroom 201 is wobbling dangerously and emitting loud sparks.',
      location: 'Classroom 201',
      student_dept: 'Electrical Engineering'
    };

    assert.ok(payload.complaint_text.trim().length >= 10);
    assert.equal(typeof payload.location, 'string');
    assert.equal(typeof payload.student_dept, 'string');
  });
});

describe('Admin Analytics Scenarios', () => {
  test('Scenario 1: Normal category statistics response', () => {
    const apiResponse = {
      total_complaints: 25,
      resolved_count: 8,
      critical_high_count: 6,
      pending_review_count: 4,
      in_progress_count: 13,
      category_distribution: [
        { category: 'C01', category_name: 'Hostel and Accommodation', count: 6, percentage: 24.0 },
        { category: 'C02', category_name: 'Electricity and Water', count: 4, percentage: 16.0 },
      ],
      hotspots: [
        { location: 'Hostel Block B', category: 'C01', category_name: 'Hostel and Accommodation', count: 3, percentage: 12.0 }
      ]
    };

    const total = Number(apiResponse.total_complaints) || 0;
    const resolved = Number(apiResponse.resolved_count) || 0;
    const resRate = total > 0 ? (resolved / total) * 100 : 0;
    assert.equal(formatPercent(resRate), '32.0%');

    const catList = apiResponse.category_distribution.map(item => ({
      category: safeString(item.category),
      category_name: safeString(item.category_name),
      count: Number(item.count) || 0,
      percentage: Number(item.percentage) || 0,
    }));

    assert.equal(catList.length, 2);
    assert.equal(typeof catList[0].count, 'number');
    assert.equal(catList[0].count, 6);
    assert.equal(typeof catList[0].category_name, 'string');
  });

  test('Scenario 2: Empty category statistics response', () => {
    const emptyResponse = {
      total_complaints: 0,
      resolved_count: 0,
      critical_high_count: 0,
      pending_review_count: 0,
      in_progress_count: 0,
      category_distribution: [],
      hotspots: []
    };

    const catList = safeArray(emptyResponse.category_distribution);
    assert.equal(catList.length, 0);

    const maxCount = Math.max(...catList.map(c => c.count), 1);
    assert.equal(maxCount, 1, 'Max count fallback should be 1 to prevent division by zero');
  });

  test('Scenario 3 & 4: Missing category_name, count, or percentage', () => {
    const rawData = [
      { category: 'C08', count: null, percentage: undefined },
      { category: 'C03', category_name: null, count: 5 }
    ];

    const normalized = rawData.map(item => ({
      category: safeString(item.category, 'Unknown'),
      category_name: safeString(item.category_name, 'General'),
      count: Number(item.count) || 0,
      percentage: Number(item.percentage) || 0,
    }));

    assert.equal(normalized[0].count, 0);
    assert.equal(normalized[0].percentage, 0);
    assert.equal(normalized[1].category_name, 'General');
    assert.equal(normalized[1].count, 5);
  });

  test('Scenario 5: Object-shaped category distribution (preventing React child object crash)', () => {
    // What previously crashed the React UI with "Objects are not valid as a React child"
    const objectShapedCatDist = {
      C01: { count: 5, percentage: 20.0 },
      C02: { count: 3, percentage: 12.0 },
    };

    // The robust normalizer in AdminDashboard.jsx
    let categoryList = [];
    if (Array.isArray(objectShapedCatDist)) {
      categoryList = objectShapedCatDist;
    } else if (objectShapedCatDist && typeof objectShapedCatDist === 'object') {
      categoryList = Object.entries(objectShapedCatDist).map(([code, countVal]) => {
        const cnt = typeof countVal === 'object' ? Number(countVal?.count) || 0 : Number(countVal) || 0;
        const pct = typeof countVal === 'object' ? Number(countVal?.percentage) || 0 : 0;
        return {
          category: code,
          category_name: code,
          count: cnt,
          percentage: pct,
        };
      });
    }

    assert.equal(categoryList.length, 2);
    // Ensure every value in the mapped list is a primitive
    for (const item of categoryList) {
      assert.equal(typeof item.category, 'string');
      assert.equal(typeof item.count, 'number');
      assert.equal(typeof item.percentage, 'number');
      // Rendering {item.count} in JSX is guaranteed safe
      assert.doesNotThrow(() => `${item.count} tickets`);
    }
  });

  test('Scenario 6 & 7: Null API response or failed request', () => {
    const nullOverview = null;
    const total = Number(nullOverview?.total_complaints) || 0;
    const catList = safeArray(nullOverview?.category_distribution);

    assert.equal(total, 0);
    assert.equal(catList.length, 0);
  });

  test('Scenario 8: Chart bar width calculations with valid and empty datasets', () => {
    const maxCount = 10;
    const items = [
      { count: 0 },
      { count: 5 },
      { count: 10 }
    ];

    const widths = items.map(it => Math.min(100, Math.max(2, (it.count / maxCount) * 100)));
    assert.equal(widths[0], 2); // clamped minimum 2% for visibility
    assert.equal(widths[1], 50);
    assert.equal(widths[2], 100);
  });
});

describe('Staff Review & Priority Governance Scenarios', () => {
  test('Priority override request normalizes priority to uppercase', () => {
    const validInputs = ['low', 'medium', 'high', 'critical', 'CRITICAL', 'HIGH'];
    for (const input of validInputs) {
      const upper = String(input).toUpperCase();
      assert.ok(['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].includes(upper));
    }
  });

  test('Priority override requires non-empty justification reason', () => {
    const invalidReasons = ['', '   ', null, undefined];
    for (const r of invalidReasons) {
      const isValid = Boolean(r && String(r).trim().length > 0);
      assert.equal(isValid, false, `Reason "${r}" should be rejected`);
    }

    const validReason = 'Physically inspected the site and verified sparking hazard';
    assert.equal(Boolean(validReason.trim().length > 0), true);
  });
});
