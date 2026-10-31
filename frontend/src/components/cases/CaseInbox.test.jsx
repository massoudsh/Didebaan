import test, { beforeEach, afterEach } from 'node:test';
import assert from 'node:assert/strict';
import { act, create } from 'react-test-renderer';
import CaseInbox, { caseQueue } from './CaseInbox.jsx';
import { api } from '../../api.js';

let renderer;
const originals = { ...api };
const text = (node) => node.children.map((child) => (typeof child === 'string' ? child : text(child))).join('');
const button = (label) => renderer.root.findAllByType('button').find((item) => text(item) === label);

const escalated = [
  { alert_id: 'A1', title: 'Low and old', severity: 'LOW', status: 'ESCALATED', assigned_to: 'alice', created_at: '2026-10-01T00:00:00Z' },
  { alert_id: 'A2', title: 'Critical and new', severity: 'CRITICAL', status: 'ESCALATED', assigned_to: 'alice', created_at: '2026-10-30T00:00:00Z' },
];

beforeEach(() => {
  api.alerts = async (params) => ({
    count: params.status === 'ESCALATED' ? escalated.length : 0,
    results: params.status === 'ESCALATED' ? escalated : [],
    next: null,
  });
  api.comments = async () => [];
});
afterEach(() => {
  if (renderer) act(() => renderer.unmount());
  renderer = undefined;
  Object.assign(api, originals);
});

test('caseQueue maps status and ownership onto inbox queues', () => {
  assert.equal(caseQueue({ status: 'RESOLVED', assigned_to: 'alice' }), 'closed');
  assert.equal(caseQueue({ status: 'FALSE_POSITIVE' }), 'closed');
  assert.equal(caseQueue({ status: 'OPEN' }), 'unowned');
  assert.equal(caseQueue({ status: 'UNDER_REVIEW', assigned_to: 'alice' }), 'review');
  assert.equal(caseQueue({ status: 'ESCALATED', assigned_to: 'alice' }), 'needs-action');
});

test('needs-action queue requests escalated cases owned by the current user and sorts by severity', async () => {
  const calls = [];
  api.alerts = async (params) => { calls.push(params); return { count: 0, results: escalated, next: null }; };
  await act(async () => { renderer = create(<CaseInbox currentUser="alice" roles={['INVESTIGATOR']} />); });
  assert.equal(calls[0].status, 'ESCALATED');
  assert.equal(calls[0].assigned_to, 'alice');
  const idCells = renderer.root.findAllByType('td').map((cell) => text(cell)).filter((value) => /^A\d$/.test(value));
  assert.deepEqual(idCells, ['A2', 'A1']);
});

test('unowned queue requests unassigned open cases', async () => {
  const calls = [];
  api.alerts = async (params) => { calls.push(params); return { count: 0, results: [], next: null }; };
  await act(async () => { renderer = create(<CaseInbox currentUser="alice" roles={['SUPERVISOR']} />); });
  await act(async () => button('بدون مالک').props.onClick());
  const last = calls.at(-1);
  assert.equal(last.status, 'OPEN');
  assert.equal(last.unassigned, '1');
});

test('opening a case shows review actions only for its owner', async () => {
  await act(async () => { renderer = create(<CaseInbox currentUser="bob" roles={['INVESTIGATOR']} />); });
  const row = renderer.root.findAll((node) => node.type === 'tr' && typeof node.props.onClick === 'function' && node.props.tabIndex === 0)
    .find((node) => text(node).includes('A2'));
  await act(async () => row.props.onClick({}));
  assert.equal(button('حل‌شده (حل‌شده)'), undefined);
  assert.ok(renderer.root.findAll((node) => node.props.role === 'dialog').length > 0);
});
