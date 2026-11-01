import { test, describe } from 'node:test';
import assert from 'node:assert/strict';
import { 
  formatNumber, 
  formatPercent, 
  formatDate, 
  safeArray, 
  safeObject, 
  safeString, 
  normalizePriority, 
  normalizeStatus 
} from '../src/utils/formatters.js';

describe('Formatters & Normalization Utilities', () => {
  describe('formatNumber', () => {
    test('formats valid numeric values to given decimal places', () => {
      assert.equal(formatNumber(42.567, 1), '42.6');
      assert.equal(formatNumber(100, 0), '100');
      assert.equal(formatNumber('85.4', 2), '85.40');
      assert.equal(formatNumber(0, 1), '0.0');
    });

    test('safely handles null, undefined, empty, and NaN values', () => {
      assert.equal(formatNumber(undefined), '0.0');
      assert.equal(formatNumber(null), '0.0');
      assert.equal(formatNumber(''), '0.0');
      assert.equal(formatNumber(NaN), '0.0');
      assert.equal(formatNumber('not-a-number'), '0.0');
      assert.equal(formatNumber(undefined, 2, 'N/A'), 'N/A');
    });
  });

  describe('formatPercent', () => {
    test('formats 0 to 1 ratios to percentage string', () => {
      assert.equal(formatPercent(0.852, 1), '85.2%');
      assert.equal(formatPercent(1.0, 0), '100%');
      assert.equal(formatPercent(0.05, 1), '5.0%');
    });

    test('formats 0 to 100 percentage values without double multiplying', () => {
      assert.equal(formatPercent(85.2, 1), '85.2%');
      assert.equal(formatPercent(99.9, 0), '100%');
    });

    test('safely handles null, undefined, and NaN', () => {
      assert.equal(formatPercent(undefined), '0.0%');
      assert.equal(formatPercent(null), '0.0%');
      assert.equal(formatPercent('invalid', 1, '—'), '—');
    });
  });

  describe('formatDate', () => {
    test('formats valid ISO date strings', () => {
      const formatted = formatDate('2026-11-01T10:00:00Z');
      assert.notEqual(formatted, '—');
      assert.ok(formatted.includes('2026'));
    });

    test('returns fallback for invalid or missing dates', () => {
      assert.equal(formatDate(null), '—');
      assert.equal(formatDate(undefined), '—');
      assert.equal(formatDate('invalid-date'), '—');
    });
  });

  describe('safeArray & safeObject & safeString', () => {
    test('safeArray returns arrays or empty array fallback', () => {
      assert.deepEqual(safeArray([1, 2, 3]), [1, 2, 3]);
      assert.deepEqual(safeArray(null), []);
      assert.deepEqual(safeArray(undefined), []);
      assert.deepEqual(safeArray({ not: 'an array' }), []);
      assert.deepEqual(safeArray('string'), []);
    });

    test('safeObject returns objects or empty object fallback', () => {
      assert.deepEqual(safeObject({ a: 1 }), { a: 1 });
      assert.deepEqual(safeObject(null), {});
      assert.deepEqual(safeObject(undefined), {});
      assert.deepEqual(safeObject([1, 2]), {});
      assert.deepEqual(safeObject('string'), {});
    });

    test('safeString returns non-empty strings or fallback', () => {
      assert.equal(safeString('Hello'), 'Hello');
      assert.equal(safeString(''), '—');
      assert.equal(safeString('   '), '—');
      assert.equal(safeString(null), '—');
      assert.equal(safeString(undefined, 'Fallback'), 'Fallback');
    });
  });

  describe('normalizePriority & normalizeStatus', () => {
    test('normalizes priorities to lowercase keys', () => {
      assert.equal(normalizePriority('CRITICAL'), 'critical');
      assert.equal(normalizePriority('high'), 'high');
      assert.equal(normalizePriority('MEDIUM'), 'medium');
      assert.equal(normalizePriority('low'), 'low');
      assert.equal(normalizePriority(null), 'medium');
      assert.equal(normalizePriority('UNKNOWN'), 'medium');
    });

    test('normalizes statuses to lowercase keys', () => {
      assert.equal(normalizeStatus('SUBMITTED'), 'submitted');
      assert.equal(normalizeStatus('in_progress'), 'in_progress');
      assert.equal(normalizeStatus('RESOLVED'), 'resolved');
      assert.equal(normalizeStatus(null), 'submitted');
    });
  });
});

