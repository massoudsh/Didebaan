import test from 'node:test';
import assert from 'node:assert/strict';
import { outcomeRate } from './Dashboard.jsx';

test('false-positive rate is measured over final outcomes only', () => {
  assert.deepEqual(outcomeRate({ by_status: { RESOLVED: 6, FALSE_POSITIVE: 2, OPEN: 40 } }), { rate: 25, reviewed: 8 });
});

test('false-positive rate is unavailable before the first final decision', () => {
  assert.equal(outcomeRate({ by_status: { OPEN: 10, UNDER_REVIEW: 3, ESCALATED: 1 } }), null);
  assert.equal(outcomeRate(undefined), null);
});
