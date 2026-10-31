import test, { beforeEach, afterEach } from 'node:test';
import assert from 'node:assert/strict';
import { act, create } from 'react-test-renderer';
import AlertQueue from './AlertQueue.jsx';
import { api } from '../api.js';

let renderer;
const originals = { ...api };
const text = (node) => node.children.map((child) => typeof child === 'string' ? child : text(child)).join('');
const button = (label) => renderer.root.findAllByType('button').find((item) => text(item) === label);
const openRow = async (id) => {
  const link = renderer.root.findAllByType('button').find((item) => text(item) === id);
  await act(async () => link.props.onClick({ stopPropagation() {} }));
};
const alerts = [
  { alert_id: 'A1', title: 'Mine', assigned_to: 'alice', severity: 'HIGH', status: 'OPEN', risk_score: 80,
    explanation: [{ rule_name: 'Actual rule name', reason: 'Reason', weight: 2 }] },
  { alert_id: 'A2', title: 'Another case', assigned_to: 'bob', severity: 'HIGH', status: 'OPEN', risk_score: 80 },
];

beforeEach(() => {
  globalThis.window = { addEventListener() {}, removeEventListener() {} };
  globalThis.document = { activeElement: null, addEventListener() {}, removeEventListener() {}, body: { style: {} } };
  api.alerts = async () => ({ count: 2, results: alerts, next: null });
  api.comments = async () => [];
  api.relatedAlerts = async () => ({ results: [] });
});
afterEach(() => {
  if (renderer) act(() => renderer.unmount());
  renderer = undefined;
  Object.assign(api, originals);
  delete globalThis.window;
  delete globalThis.document;
});
const mount = async (roles = ['INVESTIGATOR']) => act(async () => { renderer = create(<AlertQueue currentUser="alice" roles={roles} />); });

test('investigators can review only their assigned cases and see real explanation fields', async () => {
  await mount();
  await openRow('A1');
  assert.ok(button('ثبت تصمیم'));
  assert.ok(JSON.stringify(renderer.toJSON()).includes('Actual rule name'));
  assert.ok(JSON.stringify(renderer.toJSON()).includes('وزن قانون'));
  await act(async () => renderer.root.findByProps({ 'aria-label': 'بستن' }).props.onClick());
  await openRow('A2');
  assert.equal(button('ثبت تصمیم'), undefined);
  assert.equal(button('افزودن یادداشت'), undefined);
});

test('supervisors retain review access to cases assigned to other investigators', async () => {
  await mount(['SUPERVISOR']);
  await openRow('A2');
  assert.ok(button('ثبت تصمیم'));
  assert.ok(button('ثبت ارجاع'));
});

test('export preserves the queue assignee and ordering filters', async () => {
  let params;
  api.exportAlerts = async (value) => { params = value; };
  await mount();
  await act(async () => renderer.root.findAllByType('select')[2].props.onChange({ target: { value: 'me' } }));
  await act(async () => renderer.root.findAllByType('select')[3].props.onChange({ target: { value: '-risk_score' } }));
  await act(async () => button('خروجی هشدارها (CSV)').props.onClick());
  assert.equal(params.assigned_to, 'alice');
  assert.equal(params.ordering, '-risk_score');
  assert.equal(params.export_format, 'csv');
});

test('debounced search clears bulk selection to prevent acting on hidden cases', async () => {
  await mount(['SUPERVISOR']);
  const checkbox = renderer.root.findByProps({ 'aria-label': 'انتخاب A1' });
  await act(async () => checkbox.props.onChange());
  assert.equal(renderer.root.findAllByProps({ 'aria-label': 'عملیات گروهی' }).length, 1);
  const search = renderer.root.findByProps({ placeholder: 'شناسه، عنوان یا توضیح' });
  await act(async () => {
    search.props.onChange({ target: { value: 'other' } });
  });
  await act(async () => new Promise((resolve) => setTimeout(resolve, 450)));
  assert.equal(renderer.root.findAllByProps({ 'aria-label': 'عملیات گروهی' }).length, 0);
});
