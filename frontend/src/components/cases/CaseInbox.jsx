import { useCallback, useEffect, useState } from 'react';
import { api } from '../../api.js';
import { fmtAge, fmtDate, fmtNumber, STATUS_LABELS, SEVERITY_LABELS } from '../../format.js';
import { Badge, Button, DataTable, ErrorState, TableSkeleton } from '../ui.jsx';
import CaseDetail from './CaseDetail.jsx';

const PAGE_SIZE = 20;
const PRIORITY = { CRITICAL: 0, HIGH: 1, MEDIUM: 2, LOW: 3 };

const QUEUES = [
  { id: 'needs-action', label: 'نیازمند اقدام', description: 'پرونده‌های ارجاع‌شده به من که بدون تصمیم نهایی باقی مانده‌اند.' },
  { id: 'review', label: 'در بررسی', description: 'پرونده‌های ارجاع‌شده که هنوز به نتیجه نرسیده‌اند.' },
  { id: 'unowned', label: 'بدون مالک', description: 'پرونده‌های باز بدون بررسی‌کننده؛ برای ارجاع.' },
  { id: 'closed', label: 'بسته‌شده', description: 'پرونده‌های حل‌شده یا مثبت کاذب.' },
];

export function caseQueue(alert) {
  if (['RESOLVED', 'FALSE_POSITIVE'].includes(alert.status)) return 'closed';
  if (!alert.assigned_to) return 'unowned';
  if (alert.status === 'ESCALATED') return 'needs-action';
  return alert.status === 'UNDER_REVIEW' ? 'review' : 'needs-action';
}

export default function CaseInbox({ roles = [], currentUser, initial }) {
  const canAssign = roles.includes('SUPERVISOR') || roles.includes('COMPLIANCE_OFFICER');
  const [queue, setQueue] = useState(initial?.queue || 'needs-action');
  const [onlyMine, setOnlyMine] = useState(false);
  const [items, setItems] = useState([]);
  const [count, setCount] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [openCase, setOpenCase] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const base = { ordering: '-created_at' };
      if (onlyMine || queue === 'needs-action') base.assigned_to = currentUser;
      if (queue === 'unowned') base.unassigned = '1';
      const requests = queue === 'closed'
        ? [api.alerts({ ...base, status: 'RESOLVED' }), api.alerts({ ...base, status: 'FALSE_POSITIVE' })]
        : [api.alerts({ ...base, status: { review: 'UNDER_REVIEW', unowned: 'OPEN', 'needs-action': 'ESCALATED' }[queue] })];
      const pages = await Promise.all(requests);
      const merged = pages.flatMap((page) => page.results);
      const sort = (a, b) => (PRIORITY[a.severity] ?? 9) - (PRIORITY[b.severity] ?? 9) || new Date(a.created_at) - new Date(b.created_at);
      setItems([...merged].sort(sort).slice(0, PAGE_SIZE));
      setCount(pages.reduce((sum, page) => sum + page.count, 0));
      setError('');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [queue, onlyMine, currentUser]);

  useEffect(() => { load(); }, [load]);

  useEffect(() => {
    if (initial?.alertId) api.alert(initial.alertId).then(setOpenCase).catch((err) => setError(err.message));
  }, [initial?.alertId]);

  function updateCase(updated) {
    setOpenCase(updated);
    setItems((current) => current.map((item) => (item.alert_id === updated.alert_id ? updated : item)));
  }

  const active = QUEUES.find((item) => item.id === queue);

  const columns = [
    { key: 'severity', header: 'اولویت', render: (alert) => <Badge kind="sev" value={alert.severity} labels={SEVERITY_LABELS} /> },
    { key: 'alert_id', header: 'پرونده', render: (alert) => <span className="mono">{alert.alert_id}</span> },
    { key: 'title', header: 'موضوع', className: 'title-cell', render: (alert) => alert.title },
    { key: 'customer', header: 'مشتری', render: (alert) => alert.customer_detail ? `${alert.customer_detail.first_name} ${alert.customer_detail.last_name}` : '—' },
    { key: 'status', header: 'وضعیت', render: (alert) => <Badge kind="st" value={alert.status} labels={STATUS_LABELS} /> },
    { key: 'assigned_to', header: 'مالک', render: (alert) => alert.assigned_to ? <span dir="ltr">{alert.assigned_to}</span> : <span className="muted">بدون مالک</span> },
    { key: 'opened', header: 'باز شده', render: (alert) => fmtDate(alert.created_at) },
    { key: 'last', header: 'آخرین فعالیت', render: (alert) => alert.assigned_at ? `${fmtAge(alert.assigned_at)} پیش` : '—' },
  ];

  return (
    <section>
      <div className="page-head">
        <div>
          <h2>کارتابل پرونده‌ها</h2>
          <p className="muted">ردیابی پرونده از هشدار تا تصمیم؛ اولویت اول، کم‌سن‌ترین پرونده با شدت بالاتر است.</p>
        </div>
        <Button onClick={load} loading={loading}>تازه‌سازی</Button>
      </div>

      <div className="saved-views" role="group" aria-label="صندوق پرونده‌ها">
        {QUEUES.map((item) => (
          <button key={item.id} type="button" className={`chip-btn${queue === item.id ? ' active' : ''}`} aria-pressed={queue === item.id} onClick={() => { setQueue(item.id); setOnlyMine(item.id === 'needs-action' ? onlyMine : false); }}>
            {item.label}
          </button>
        ))}
        {queue !== 'needs-action' && (
          <label className="chip" style={{ gap: '.4rem', cursor: 'pointer' }}>
            <input type="checkbox" checked={onlyMine} onChange={(event) => setOnlyMine(event.target.checked)} style={{ width: 'auto', minHeight: 'auto' }} />
            فقط پرونده‌های من
          </label>
        )}
      </div>

      <p className="muted">{active.description}{count !== null && !loading ? ` · ${fmtNumber(count)} هشدار در این فیلتر` : ''}</p>

      {error && <ErrorState message={error} onRetry={load} />}

      <div className="card" style={{ overflow: 'hidden' }}>
        {loading && !items.length ? <TableSkeleton rows={6} columns={7} /> : (
          <DataTable
            columns={columns}
            rows={items}
            rowKey={(alert) => alert.alert_id}
            empty={queue === 'needs-action' ? 'پروندهٔ ارجاع‌شده‌ای نیاز به اقدام شما ندارد.' : 'پرونده‌ای در این صندوق نیست.'}
            onRowClick={(alert) => setOpenCase(alert)}
            caption={`صندوق ${active.label}`}
          />
        )}
      </div>

      {queue === 'needs-action' && <p className="muted">پرونده‌های «نیازمند اقدام» بر اساس هشدارهای ارجاع‌شدهٔ ارتقایافته، باز و تحت بررسی مرتب شده‌اند. برای دیدن همهٔ ارجاع‌شدگان از «در بررسی» استفاده کنید.</p>}

      {openCase && (
        <CaseDetail
          alert={openCase}
          currentUser={currentUser}
          canAssign={canAssign}
          canReview={roles.includes('INVESTIGATOR') ? openCase.assigned_to === currentUser : roles.includes('SUPERVISOR') || roles.includes('COMPLIANCE_OFFICER')}
          onClose={() => setOpenCase(null)}
          onChanged={updateCase}
        />
      )}
    </section>
  );
}
