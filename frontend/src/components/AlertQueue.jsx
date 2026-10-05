import { useEffect, useState } from 'react';
import { api } from '../api.js';
import {
  fmtAge, fmtDate, fmtNumber, fmtScore,
  REVIEW_STATUSES, SEVERITY_LABELS, STATUS_LABELS,
} from '../format.js';
import AlertDetail from './AlertDetail.jsx';

const PAGE_SIZE = 20;

export function Badge({ kind, value, labels }) {
  return <span className={`badge ${kind}-${value}`}>{labels[value] || value}</span>;
}

export default function AlertQueue({ currentUser }) {
  const [filters, setFilters] = useState({ status: '', severity: '', assignee: '', ordering: '-created_at' });
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
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => {
      setSearch(searchInput.trim());
      setPage(1);
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

  const reload = () => setReloadKey((key) => key + 1);

  function changeFilter(name, value) {
    setFilters((current) => ({ ...current, [name]: value }));
    setPage(1);
    setSelected(new Set());
  }

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

  async function runBulk(action) {
    setBusy(true);
    setNotice('');
    setError('');
    const ids = [...selected];
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
      const format = 'csv';
      if (kind === 'alerts') {
        await api.exportAlerts({ export_format: format, status: filters.status, severity: filters.severity });
      } else {
        await api.exportComments({ export_format: format });
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

  const pages = Math.max(1, Math.ceil(data.count / PAGE_SIZE));

  return (
    <section>
      <div className="page-head">
        <div>
          <h2>صف هشدارها</h2>
          <p className="muted">{fmtNumber(data.count)} هشدار مطابق فیلترها</p>
        </div>
        <div className="row-gap">
          <button className="btn" onClick={() => exportData('alerts')}>خروجی هشدارها (CSV)</button>
          <button className="btn" onClick={() => exportData('comments')}>خروجی تاریخچهٔ پرونده‌ها (CSV)</button>
        </div>
      </div>

      <div className="filters card">
        <label>
          جست‌وجو
          <input value={searchInput} onChange={(e) => setSearchInput(e.target.value)} placeholder="شناسه، عنوان یا توضیح" />
        </label>
        <label>
          وضعیت
          <select value={filters.status} onChange={(e) => changeFilter('status', e.target.value)}>
            <option value="">همه</option>
            {Object.entries(STATUS_LABELS).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
          </select>
        </label>
        <label>
          شدت
          <select value={filters.severity} onChange={(e) => changeFilter('severity', e.target.value)}>
            <option value="">همه</option>
            {Object.entries(SEVERITY_LABELS).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
          </select>
        </label>
        <label>
          بررسی‌کننده
          <select value={filters.assignee} onChange={(e) => changeFilter('assignee', e.target.value)}>
            <option value="">همه</option>
            <option value="me">ارجاع‌شده به من</option>
            <option value="none">بدون بررسی‌کننده</option>
          </select>
        </label>
        <label>
          مرتب‌سازی
          <select value={filters.ordering} onChange={(e) => changeFilter('ordering', e.target.value)}>
            <option value="-created_at">جدیدترین</option>
            <option value="created_at">قدیمی‌ترین</option>
            <option value="-risk_score">بیشترین امتیاز ریسک</option>
            <option value="risk_score">کمترین امتیاز ریسک</option>
          </select>
        </label>
      </div>

      {notice && <p className="notice" role="status">{notice}</p>}
      {error && <p className="error" role="alert">{error}</p>}

      {selected.size > 0 && (
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
              <button className="btn" disabled={busy} onClick={() => setBulk({ ...bulk, assignee: currentUser })}>خودم</button>
              <button className="btn primary" disabled={busy} onClick={() => runBulk('assign')}>ارجاع</button>
            </div>
            <div className="bulk-group">
              <select value={bulk.status} onChange={(e) => setBulk({ ...bulk, status: e.target.value })} aria-label="وضعیت جدید">
                {REVIEW_STATUSES.map((value) => <option key={value} value={value}>{STATUS_LABELS[value]}</option>)}
              </select>
              <button className="btn primary" disabled={busy} onClick={() => runBulk('review')}>ثبت بازبینی</button>
            </div>
            <input
              className="grow"
              value={bulk.notes}
              onChange={(e) => setBulk({ ...bulk, notes: e.target.value })}
              placeholder="توضیحات (در تاریخچهٔ هر پرونده ثبت می‌شود)"
              aria-label="توضیحات"
            />
            <button className="btn ghost" onClick={() => setSelected(new Set())}>لغو انتخاب</button>
          </div>
        </div>
      )}

      <div className="table-wrap card">
        <table>
          <thead>
            <tr>
              <th className="narrow"><input type="checkbox" checked={allSelected} onChange={toggleAll} aria-label="انتخاب همهٔ ردیف‌های صفحه" /></th>
              <th>شناسه</th>
              <th>عنوان</th>
              <th>مشتری</th>
              <th>شدت</th>
              <th>وضعیت</th>
              <th>امتیاز</th>
              <th>بررسی‌کننده</th>
              <th>زمان ثبت</th>
            </tr>
          </thead>
          <tbody>
            {data.results.map((alert) => (
              <tr
                key={alert.alert_id}
                className={selected.has(alert.alert_id) ? 'selected' : ''}
                onClick={() => setOpenAlert(alert)}
              >
                <td className="narrow" onClick={(e) => e.stopPropagation()}>
                  <input
                    type="checkbox"
                    checked={selected.has(alert.alert_id)}
                    onChange={() => toggle(alert.alert_id)}
                    aria-label={`انتخاب ${alert.alert_id}`}
                  />
                </td>
                <td dir="ltr" className="mono">
                  <button className="link" onClick={() => setOpenAlert(alert)}>{alert.alert_id}</button>
                </td>
                <td className="title-cell">{alert.title}</td>
                <td>{alert.customer_detail ? `${alert.customer_detail.first_name} ${alert.customer_detail.last_name}` : '—'}</td>
                <td><Badge kind="sev" value={alert.severity} labels={SEVERITY_LABELS} /></td>
                <td><Badge kind="st" value={alert.status} labels={STATUS_LABELS} /></td>
                <td>{fmtScore(alert.risk_score)}</td>
                <td>
                  {alert.assigned_to ? (
                    <>
                      <span dir="ltr">{alert.assigned_to}</span>
                      <small className="muted block">از {fmtAge(alert.assigned_at)} پیش</small>
                    </>
                  ) : <span className="muted">—</span>}
                </td>
                <td>{fmtDate(alert.created_at)}</td>
              </tr>
            ))}
            {!loading && data.results.length === 0 && (
              <tr><td colSpan={9} className="empty">هشداری مطابق فیلترها پیدا نشد.</td></tr>
            )}
          </tbody>
        </table>
        {loading && <p className="muted pad">در حال بارگذاری…</p>}
      </div>

      <div className="pager">
        <button className="btn" disabled={page <= 1} onClick={() => setPage(page - 1)}>قبلی</button>
        <span>صفحهٔ {fmtNumber(page)} از {fmtNumber(pages)}</span>
        <button className="btn" disabled={!data.next} onClick={() => setPage(page + 1)}>بعدی</button>
      </div>

      {openAlert && (
        <AlertDetail
          key={openAlert.alert_id}
          alert={openAlert}
          currentUser={currentUser}
          onClose={() => setOpenAlert(null)}
          onChanged={handleChanged}
        />
      )}
    </section>
  );
}
