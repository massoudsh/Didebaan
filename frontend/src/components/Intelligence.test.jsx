import test, { afterEach, beforeEach } from 'node:test';
import assert from 'node:assert/strict';
import { act, create } from 'react-test-renderer';
import { api, auth, login } from '../api.js';
import Intelligence from './Intelligence.jsx';

let renderer;
const originals = { ...api };
const text = (node) => node.children.map((child) => typeof child === 'string' ? child : text(child)).join('');
const button = (label) => renderer.root.findAllByType('button').find((node) => text(node) === label);
const changeInput = async (index, value) => act(async () => renderer.root.findAllByType('input')[index].props.onChange({ target: { value } }));
const submit = async () => act(async () => renderer.root.findByType('form').props.onSubmit({ preventDefault() {} }));
const mount = async (roles = ['COMPLIANCE_OFFICER']) => act(async () => { renderer = create(<Intelligence roles={roles} />); });

beforeEach(() => {
  const storage = new Map();
  globalThis.localStorage = {
    getItem: (key) => storage.get(key) ?? null,
    setItem: (key, value) => storage.set(key, value),
    removeItem: (key) => storage.delete(key),
  };
  api.rules = async () => ({ results: [{ id: 'rule-1', name: 'Amount', status: 'DRAFT', rule_type: 'THRESHOLD', configuration: { amount_threshold: 200 } }], next: null });
});
afterEach(() => {
  if (renderer) act(() => renderer.unmount());
  renderer = undefined;
  Object.assign(api, originals);
});

test('first login authenticates the profile request before persisting the session', async (t) => {
  const calls = [];
  t.mock.method(globalThis, 'fetch', async (path, options) => {
    calls.push({ path, options });
    assert.equal(auth.token, null);
    return new Response(JSON.stringify(path.endsWith('/token/')
      ? { token: 'test-session' }
      : { username: 'reviewer', roles: ['AUDITOR'] }), { status: 200 });
  });
  const profile = await login('reviewer', 'test-password');
  assert.equal(calls[0].options.headers.Authorization, undefined);
  assert.equal(calls[1].options.headers.Authorization, 'Token test-session');
  assert.equal(profile.username, 'reviewer');
  assert.equal(auth.token, 'test-session');
  assert.deepEqual(auth.roles, ['AUDITOR']);
});

test('failed profile lookup does not save an incomplete session', async (t) => {
  t.mock.method(globalThis, 'fetch', async (path) => new Response(JSON.stringify(
    path.endsWith('/token/') ? { token: 'test-session' } : { detail: 'Unavailable' }
  ), { status: path.endsWith('/token/') ? 200 : 503 }));
  await assert.rejects(login('reviewer', 'test-password'));
  assert.equal(auth.token, null);
});

test('auditor sees graph, SLA and export, not compliance-only actions', async () => {
  await mount(['AUDITOR']);
  assert.ok(button('شبکهٔ ارتباطات'));
  assert.ok(button('مهلت رسیدگی'));
  assert.ok(button('بستهٔ شواهد'));
  assert.equal(button('آزمایش قوانین'), undefined);
  assert.equal(button('غربالگری فارسی'), undefined);
});

test('graph submits customer and range, renders edges, peers and truncation', async () => {
  let args;
  api.graph = async (params) => {
    args = params;
    return { sampled_count: 200, eligible_count: 300, truncated: true,
      nodes: [{ id: 'customer:C-1', kind: 'customer', label: 'C-1' }, { id: 'device:D-1', kind: 'device', label: 'D-1' }],
      edges: [{ source: 'customer:C-1', target: 'device:D-1', transactions: 2 }],
      related_customers: [{ customer__customer_id: 'C-2', transactions: 1 }], related_truncated: false };
  };
  await mount();
  await changeInput(0, ' C-1 ');
  await submit();
  assert.deepEqual(args, { customer_id: 'C-1', days: 30 });
  assert.equal(renderer.root.findAllByType('svg').length, 1);
  assert.ok(JSON.stringify(renderer.toJSON()).includes('D-1'));
  assert.ok(JSON.stringify(renderer.toJSON()).includes('C-2'));
  assert.ok(JSON.stringify(renderer.toJSON()).includes('نتایج محدود به نمونه'));
});

test('graph errors are visible and successful empty result can be retried', async () => {
  api.graph = async () => { throw new Error('Customer not found'); };
  await mount();
  await changeInput(0, 'missing');
  await submit();
  assert.equal(text(renderer.root.findByProps({ role: 'alert' })), 'Customer not found');
  api.graph = async () => ({ sampled_count: 0, eligible_count: 0, nodes: [], edges: [], related_customers: [] });
  await submit();
  assert.equal(renderer.root.findAllByProps({ role: 'alert' }).length, 0);
  assert.ok(JSON.stringify(renderer.toJSON()).includes('ارتباطی در این بازه پیدا نشد'));
});

test('simulation rejects malformed JSON locally, then sends selected rule configuration', async () => {
  let args;
  api.simulate = async (data) => {
    args = data;
    return { evaluated_count: 0, eligible_count: 0, rule_version: 1, baseline_matches: 0,
      candidate_matches: 0, new_matches: 0, removed_matches: 0, results: [] };
  };
  await mount();
  await act(async () => button('آزمایش قوانین').props.onClick());
  await act(async () => renderer.root.findAllByType('select')[0].props.onChange({ target: { value: 'rule-1' } }));
  await act(async () => renderer.root.findByType('textarea').props.onChange({ target: { value: '{broken' } }));
  await submit();
  assert.equal(args, undefined);
  assert.ok(text(renderer.root.findByProps({ role: 'alert' })).includes('JSON'));
  await act(async () => renderer.root.findByType('textarea').props.onChange({ target: { value: '{"amount_threshold":50}' } }));
  await submit();
  assert.deepEqual(args, { rule_id: 'rule-1', configuration: { amount_threshold: 50 }, days: 30, limit: 100 });
  assert.ok(JSON.stringify(renderer.toJSON()).includes('تراکنش تکمیل‌شده‌ای'));
});

test('screening sends Persian input and shows human-review results', async () => {
  let args;
  api.screen = async (data) => {
    args = data;
    return { screened_count: 1, match_count: 1, matches: [{ id: 1, name: 'علی کریمی', source_list: 'داخلی', match_type: 'national_id', score: 100 }] };
  };
  await mount();
  await act(async () => button('غربالگری فارسی').props.onClick());
  await changeInput(0, 'علی کریمی');
  await changeInput(1, '۰۰۱۲۳۴');
  await submit();
  assert.deepEqual(args, { name: 'علی کریمی', national_id: '۰۰۱۲۳۴', minimum_score: 85 });
  assert.ok(JSON.stringify(renderer.toJSON()).includes('شناسهٔ ملی یکسان'));
});

test('SLA renders empty report and exports call the download API', async () => {
  api.sla = async () => ({ as_of: '2026-10-31T12:00:00Z', sla_hours: 24, assigned_open: 0, overdue: 0, due_soon: 0, unassigned_open: 0, results: [] });
  let exported;
  api.exportCase = async (id) => { exported = id; };
  await mount(['AUDITOR']);
  await act(async () => button('مهلت رسیدگی').props.onClick());
  await submit();
  assert.ok(JSON.stringify(renderer.toJSON()).includes('پروندهٔ باز ارجاع‌شده‌ای وجود ندارد'));
  await act(async () => button('بستهٔ شواهد').props.onClick());
  await changeInput(0, ' A-1 ');
  await submit();
  assert.equal(exported, 'A-1');
  assert.ok(JSON.stringify(renderer.toJSON()).includes('برای دانلود ارسال شد'));
});

test('busy state disables tool switching while a request is pending', async () => {
  let resolve;
  api.graph = () => new Promise((done) => { resolve = done; });
  await mount(['AUDITOR']);
  await changeInput(0, 'C-1');
  act(() => { renderer.root.findByType('form').props.onSubmit({ preventDefault() {} }); });
  assert.equal(button('مهلت رسیدگی').props.disabled, true);
  assert.equal(renderer.root.findByType('form').props['aria-busy'], true);
  await act(async () => resolve({ sampled_count: 0, eligible_count: 0, nodes: [], edges: [], related_customers: [] }));
  assert.equal(button('مهلت رسیدگی').props.disabled, false);
});
