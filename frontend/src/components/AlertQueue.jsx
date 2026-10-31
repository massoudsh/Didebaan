import { useEffect, useMemo, useState } from 'react';
import { api } from '../api.js';
import {
  fmtAge, fmtDate, fmtNumber, fmtScore,
  REVIEW_STATUSES, SEVERITY_LABELS, STATUS_LABELS,
} from '../format.js';
import AlertDetail from './AlertDetail.jsx';
import { Badge, Button, DataTable, ErrorState, TableSkeleton } from './ui.jsx';

export { Badge };

const PAGE_SIZE = 20;
const DEFAULT_FILTERS = { status: '', severity: '', assignee: '', ordering: '-created_at' };
const SAVED_VIEWS = [
  { id: 'all', label: 'همهٔ هشدارها', filters: DEFAULT_FILTERS },
  { id: 'critical', label: 'بحرانی و باز', filters: { ...DEFAULT_FILTERS, severity: 'CRITICAL', status: 'OPEN' } },
  { id: 'unassigned', label: 'بدون بررسی‌کننده', filters: { ...DEFAULT_FILTERS, assignee: 'none' } },
  { id: 'mine', label: 'ارجاع‌شده به من', filters: { ...DEFAULT_FILTERS, assignee: 'me' } },
  { id: 'review', label: 'در حال بررسی', filters: { ...DEFAULT_FILTERS, status: 'UNDER_REVIEW' } },
];

const SORTABLE = {
  risk_score: 'risk_score',
  severity: 'severity',
  created_at: 'created_at',
};

export default function AlertQueue({ currentUser, roles = [], initial = {}, onOpenEntity }) {
  const canAssign = roles.includes('SUPERVISOR') || roles.includes('COMPLIANCE_OFFICER');
  const canReviewAny = roles.includes('SUPERVISOR') || roles.includes('COMPLIANCE_OFFICER');
  const canReviewOwn = roles.includes('INVESTIGATOR');
  const [filters, setFilters] = useState({ ...DEFAULT_FILTERS, ...(initial.filter || {}) });
  const [searchInput, setSearchInput] = useState('');
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [reloadKey, setReloadKey] = useState(0);
  const [data, setData] = useState({ count: 0, results: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [selected, setSelected] = useState(new Set());
  const [openAlert, setOpenAlert] = useState(null);
  const [bulk, setBulk] = useState({ assignee: '', status: 'UNDER_REVIEW', notes: '' });
  const [confirming, setConfirming] = useState(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => {
      setSearch(searchInput.trim());
      setPage(1);
      setSelected(new Set());
    }, 400);
    return () => clearTimeout(timer);
  }, [searchInput]);

  const queryParams = {
    status: filters.status,
    severity: filters.severity,
    assigned_to: filters.assignee === 'me' ? currentUser : '',
    unassigned: filters.assignee === 'none' ? '1' : '',
    search,
    ordering: filters.ordering,
  };

  useEffect(() => {
    let active = true;
    setLoading(true);
    api.alerts({ ...queryParams, page })
      .then((result) => {
        if (!active) return;
        setData(result);
        setError('');
      })
      .catch((err) => active && setError(err.message))
      .finally(() => active && setLoading(false));
    return () => {
      active = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters, search, page, reloadKey]);

  useEffect(() => {
    if (!initial.alertId) return;
    api.alert(initial.alertId).then(setOpenAlert).catch((err) => setError(err.message));
  }, [initial.alertId]);

  const reload = () => setReloadKey((key) => key + 1);

  useEffect(() => {
    const timer = setInterval(reload, 60000);
    return () => clearInterval(timer);
  }, []);

  function changeFilter(name, value) {
    setFilters((current) => ({ ...current, [name]: value }));
    setPage(1);
    setSelected(new Set());
  }

  function sortBy(field) {
    const current = filters.ordering;
    changeFilter('ordering', current === `-${field}` ? field : `-${field}`);
  }

  const activeView = SAVED_VIEWS.find((item) => JSON.stringify(item.filters) === JSON.stringify(filters))?.id;

  function toggle(alertId) {
    setSelected((current) => {
      const next = new Set(current);
      if (next.has(alertId)) next.delete(alertId);
      else next.add(alertId);
      return next;
    });
  }

  const pageIds = data.results.map((alert) => alert.alert_id);
  const allSelected = pageIds.length > 0 && pageIds.every((id) => selected.has(id));

  function toggleAll() {
    setSelected(allSelected ? new Set() : new Set(pageIds));
  }

  async function runBulk() {
    const action = confirming;
    setBusy(true);
    setNotice('');
    setError('');
    const ids = [...selected];
    setConfirming(null);
    try {
      const result = action === 'assign'
        ? await api.bulkAssign(ids, bulk.assignee.trim(), bulk.notes)
        : await api.bulkReview(ids, bulk.status, bulk.notes);
      const missing = result.not_found.length ? `، ${fmtNumber(result.not_found.length)} مورد پیدا نشد` : '';
      setNotice(`${fmtNumber(result.updated.length)} هشدار به‌روزرسانی شد${missing}.`);
      setSelected(new Set());
      setBulk((current) => ({ ...current, notes: '' }));
      reload();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function exportData(kind) {
    setError('');
    try {
      if (kind === 'alerts') {
        await api.exportAlerts({ export_format: 'csv', ...queryParams });
        setNotice('خروجی CSV بر اساس همان فیلترهای صف آماده شد.');
      } else {
        await api.exportComments({ export_format: 'csv' });
        setNotice('خروجی CSV تاریخچهٔ پرونده‌ها آماده شد.');
      }
    } catch (err) {
      setError(err.message);
    }
  }

  function handleChanged(updated) {
    setData((current) => ({
      ...current,
      results: current.results.map((alert) => (alert.alert_id === updated.alert_id ? updated : alert)),
    }));
    setOpenAlert(updated);
  }

  const sortState = useMemo(() => {
    const field = filters.ordering.replace('-', '');
    if (!SORTABLE[field]) return {};
    return { [field]: filters.ordering.startsWith('-') ? 'descending' : 'ascending' };
  }, [filters.ordering]);

  const pages = Math.max(1, Math.ceil(data.count / PAGE_SIZE));

  function sortLabel(label, field) {
    const state = sortState[field];
    return (
      <button type="button" className="sort-btn" onClick={() => sortBy(field)} aria-label={`مرتب‌سازی بر اساس ${label}`}>
        {label} <span aria-hidden="true">{state === 'ascending' ? '↑' : state === 'descending' ? '↓' : '↕'}</span>
      </button>
    );
  }

  const columns = [
    ...(canAssign ? [{
      key: 'select', className: 'narrow',
      header: <input type="checkbox" checked={allSelected} onChange={toggleAll} aria-label="انتخاب همهٔ ردیف‌های صفحه" onClick={(event) => event.stopPropagation()} />,
      render: (alert) => <input type="checkbox" checked={selected.has(alert.alert_id)} onChange={() => toggle(alert.alert_id)} aria-label={`انتخاب ${alert.alert_id}`} onClick={(event) => event.stopPropagation()} />,
    }] : []),
    { key: 'alert_id', header: 'شناسه', render: (alert) => <button className="link" onClick={(event) => { event.stopPropagation(); setOpenAlert(alert); }}>{alert.alert_id}</button> },
    { key: 'title', header: 'عنوان', className: 'title-cell', render: (alert) => alert.title },
    {
      key: 'customer', header: 'مشتری',
      render: (alert) => alert.customer_detail
        ? <button className="link name-link" onClick={(event) => { event.stopPropagation(); onOpenEntity?.({ kind: 'customer', id: alert.customer_detail.customer_id, label: alert.customer_detail.customer_id }); }}>
          {alert.customer_detail.first_name} {alert.customer_detail.last_name}
        </button>
        : '—',
    },
    { key: 'severity', header: sortLabel('شدت', 'severity'), render: (alert) => <Badge kind="sev" value={alert.severity} labels={SEVERITY_LABELS} /> },
    { key: 'status', header: 'وضعیت', render: (alert) => <Badge kind="st" value={alert.status} labels={STATUS_LABELS} /> },
    { key: 'risk_score', header: sortLabel('امتیاز', 'risk_score'), className: 'num', render: (alert) => fmtScore(alert.risk_score) },
    {
      key: 'assigned_to', header: 'بررسی‌کننده',
      render: (alert) => alert.assigned_to ? (
        <>
          <span dir="ltr">{alert.assigned_to}</span>
          <small className="muted block">از {fmtAge(alert.assigned_at)} پیش</small>
        </>
      ) : <span className="muted">—</span>,
    },
    { key: 'created_at', header: sortLabel('زمان ثبت', 'created_at'), render: (alert) => fmtDate(alert.created_at) },
  ];

  return (
    <section>
      <div className="page-head">
        <div>
          <h2>صف هشدارها</h2>
          <p className="muted"><span className="live-label"><span className="pulse-dot" /> زنده</span> · {fmtNumber(data.count)} هشدار مطابق فیلترها · تازه‌سازی خودکار هر ۶۰ ثانیه</p>
        </div>
        <div className="row-gap">
          <Button onClick={reload} loading={loading}>تازه‌سازی</Button>
          <Button onClick={() => exportData('alerts')}>خروجی هشدارها (CSV)</Button>
          <Button onClick={() => exportData('comments')}>خروجی تاریخچهٔ پرونده‌ها (CSV)</Button>
        </div>
      </div>

      <div className="filters card" role="group" aria-label="فیلترهای صف هشدار">
        <div className="field">
          <label htmlFor="alert-search">جست‌وجو</label>
          <input id="alert-search" value={searchInput} onChange={(e) => setSearchInput(e.target.value)} placeholder="شناسه، عنوان یا توضیح" />
        </div>
        <div className="field">
          <label htmlFor="alert-status">وضعیت</label>
          <select id="alert-status" value={filters.status} onChange={(e) => changeFilter('status', e.target.value)}>
            <option value="">همه</option>
            {Object.entries(STATUS_LABELS).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
          </select>
        </div>
        <div className="field">
          <label htmlFor="alert-severity">شدت</label>
          <select id="alert-severity" value={filters.severity} onChange={(e) => changeFilter('severity', e.target.value)}>
            <option value="">همه</option>
            {Object.entries(SEVERITY_LABELS).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
          </select>
        </div>
        <div className="field">
          <label htmlFor="alert-assignee">بررسی‌کننده</label>
          <select id="alert-assignee" value={filters.assignee} onChange={(e) => changeFilter('assignee', e.target.value)}>
            <option value="">همه</option>
            <option value="me">ارجاع‌شده به من</option>
            <option value="none">بدون بررسی‌کننده</option>
          </select>
        </div>
        <div className="field">
          <label htmlFor="alert-ordering">مرتب‌سازی</label>
          <select id="alert-ordering" value={filters.ordering} onChange={(e) => changeFilter('ordering', e.target.value)}>
            <option value="-created_at">جدیدترین</option>
            <option value="created_at">قدیمی‌ترین</option>
            <option value="-risk_score">بیشترین امتیاز ریسک</option>
            <option value="risk_score">کمترین امتیاز ریسک</option>
          </select>
        </div>
      </div>

      <div className="saved-views" role="group" aria-label="نمای‌های ذخیره‌شده">
        <span className="muted">نمای سریع:</span>
        {SAVED_VIEWS.map((item) => (
          <button key={item.id} type="button" className={`chip-btn${activeView === item.id ? ' active' : ''}`} aria-pressed={activeView === item.id} onClick={() => { setFilters({ ...item.filters }); setPage(1); setSelected(new Set()); }}>
            {item.label}
          </button>
        ))}
      </div>

      {notice && <p className="notice" role="status">{notice}</p>}
      {error && <ErrorState message={error} onRetry={reload} />}

      {canAssign && selected.size > 0 && (
        <div className="bulk card" role="region" aria-label="عملیات گروهی">
          <strong>{fmtNumber(selected.size)} هشدار انتخاب شده</strong>
          <div className="bulk-forms">
            <div className="bulk-group">
              <input
                value={bulk.assignee}
                onChange={(e) => setBulk({ ...bulk, assignee: e.target.value })}
                placeholder="نام کاربری بررسی‌کننده (خالی = لغو ارجاع)"
                dir="ltr"
                aria-label="نام کاربری بررسی‌کننده"
              />
              <Button onClick={() => setBulk({ ...bulk, assignee: currentUser })}>خودم</Button>
              <Button variant="primary" disabled={busy} onClick={() => setConfirming('assign')}>ارجاع</Button>
            </div>
            <div className="bulk-group">
              <select value={bulk.status} onChange={(e) => setBulk({ ...bulk, status: e.target.value })} aria-label="وضعیت جدید">
                {REVIEW_STATUSES.map((value) => <option key={value} value={value}>{STATUS_LABELS[value]}</option>)}
              </select>
              <Button variant="primary" disabled={busy} onClick={() => setConfirming('review')}>ثبت بازبینی</Button>
            </div>
            <input
              className="grow"
              value={bulk.notes}
              onChange={(e) => setBulk({ ...bulk, notes: e.target.value })}
              placeholder="توضیحات (در تاریخچهٔ هر پرونده ثبت می‌شود)"
              aria-label="توضیحات"
            />
            <Button variant="ghost" onClick={() => setSelected(new Set())}>لغو انتخاب</Button>
          </div>
          {confirming && (
            <div className="confirm-box" role="alertdialog" aria-label="تأیید عملیات گروهی">
              <p>
                {confirming === 'assign'
                  ? `ارجاع ${fmtNumber(selected.size)} هشدار به «${bulk.assignee.trim() || 'بدون بررسی‌کننده'}» تأیید می‌شود؟`
                  : `ثبت وضعیت «${STATUS_LABELS[bulk.status]}» برای ${fmtNumber(selected.size)} هشدار تأیید می‌شود؟`}
              </p>
              <div className="row-gap">
                <Button variant="primary" onClick={runBulk} loading={busy}>تأیید و ثبت</Button>
                <Button variant="ghost" onClick={() => setConfirming(null)}>انصراف</Button>
              </div>
            </div>
          )}
        </div>
      )}

      <div className="card" style={{ overflow: 'hidden' }}>
        {loading && !data.results.length ? <TableSkeleton rows={6} columns={8} /> : (
          <DataTable
            columns={columns}
            rows={data.results}
            rowKey={(alert) => alert.alert_id}
            empty="هشداری مطابق فیلترها پیدا نشد."
            onRowClick={(alert) => setOpenAlert(alert)}
            caption="صف هشدارها"
          />
        )}
      </div>

      <div className="pager">
        <Button disabled={page <= 1} onClick={() => setPage(page - 1)}>قبلی</Button>
        <span>صفحهٔ {fmtNumber(page)} از {fmtNumber(pages)}</span>
        <Button disabled={!data.next} onClick={() => setPage(page + 1)}>بعدی</Button>
      </div>

      {openAlert && (
        <AlertDetail
          key={openAlert.alert_id}
          alert={openAlert}
          currentUser={currentUser}
          roles={roles}
          canAssign={canAssign}
          canReview={canReviewAny || (canReviewOwn && openAlert.assigned_to === currentUser)}
          onClose={() => setOpenAlert(null)}
          onChanged={handleChanged}
          onOpenEntity={onOpenEntity}
          onOpenAlert={(alertId) => api.alert(alertId).then(setOpenAlert).catch((err) => setError(err.message))}
        />
      )}
    </section>
  );
}
