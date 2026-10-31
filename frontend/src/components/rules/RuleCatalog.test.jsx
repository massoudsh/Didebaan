import test from 'node:test';
import assert from 'node:assert/strict';
import { describeRuleConfiguration, ruleChangeSummary } from './RuleCatalog.jsx';

test('rule parameters are described in place and secrets are never rendered', () => {
  const rows = describeRuleConfiguration('THRESHOLD', { threshold: 5000000, api_secret: 's3cr3t' });
  assert.deepEqual(rows.map((row) => row.value), ['5000000', 'مقدار محرمانه — نمایش داده نمی‌شود']);
  assert.equal(rows[1].sensitive, true);
  assert.equal(JSON.stringify(rows).includes('s3cr3t'), false);
});

test('change summary lists changed parameters but excludes sensitive keys', () => {
  const changes = ruleChangeSummary(
    { threshold: 1, window_hours: 24, signing_key: 'old' },
    { threshold: 2, window_hours: 24, signing_key: 'new' },
  );
  assert.deepEqual(changes, [{ key: 'threshold', before: 1, after: 2 }]);
});

test('change summary treats missing values as changes and handles empty input', () => {
  assert.deepEqual(ruleChangeSummary({ a: 1 }, {}), [{ key: 'a', before: 1, after: undefined }]);
  assert.deepEqual(ruleChangeSummary(null, { a: 1 }), []);
});
