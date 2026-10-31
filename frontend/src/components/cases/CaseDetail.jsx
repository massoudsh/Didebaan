import { useEffect, useState } from 'react';
import { api } from '../../api.js';
import { fmtDate, STATUS_LABELS, SEVERITY_LABELS } from '../../format.js';
import { Badge, Button, IconButton } from '../ui.jsx';

const STAGES = ['OPEN', 'UNDER_REVIEW', 'ESCALATED', 'RESOLVED'];
const OUTCOMES = ['RESOLVED', 'FALSE_POSITIVE'];
const REQUIRED_NOTE = ['RESOLVED', 'FALSE_POSITIVE'];

export default function CaseDetail({ alert, currentUser, canAssign, canReview, onClose, onChanged }) {
  const [history, setHistory] = useState(null);
  const [error, setError] = useState('');
  const [drafter, setDrafter] = useState({ status: 'UNDER_REVIEW', notes: '' });
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let active = true;
    setHistory(null);
    api.comments(alert.alert_id)
      .then((items) => active && setHistory(items))
      .catch((err) => { if (active) { setHistory([]); setError(err.message); } });
    return () => { active = false; };
  }, [alert.alert_id]);

  async function save(nextStatus) {
    if (REQUIRED_NOTE.includes(nextStatus) && !drafter.notes.trim()) {
      setError('برای ثبت نتیجهٔ نهایی، دلیل تصمیم را بنویسید.');
      return;
    }
    setBusy(true);
    setError('');
    try {
      const updated = await api.review(alert.alert_id, nextStatus, drafter.notes);
      onChanged(updated);
      setDrafter({ status: nextStatus, notes: '' });
      setHistory(await api.comments(alert.alert_id));
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  const stage = alert.status === 'FALSE_POSITIVE' ? 'RESOLVED' : alert.status;
  const decisions = (history || []).filter((item) => item.comment_type === 'STATUS_CHANGE');
  const currentIndex = STAGES.indexOf(stage);

  return (
    <div className="drawer-backdrop" onClick={onClose}>
      <aside className="drawer" role="dialog" aria-modal="true" aria-labelledby="case-title" onClick={(event) => event.stopPropagation()}>
        <header className="drawer-head">
          <div>
            <h2 id="case-title">{alert.title}</h2>
            <p className="mono" dir="ltr">{alert.alert_id}</p>
          </div>
          <IconButton label="بستن" onClick={onClose}>✕</IconButton>
        </header>
        <div className="drawer-body">
          {error && <p className="error" role="alert">{error}</p>}
          <ol className="timeline" aria-label="مرحله‌های پرونده" style={{ gridTemplateColumns: `repeat(${STAGES.length}, 1fr)`, display: 'grid', gap: '.4rem' }}>
            {STAGES.map((value, index) => (
              <li key={value} style={{ borderInlineStart: 0, borderTop: `3px solid ${index <= currentIndex ? 'var(--primary)' : 'var(--border)'}`, textAlign: 'center', padding: '.5rem', fontSize: '.78rem' }}>
                {STATUS_LABELS[value]}
                {index <= currentIndex && <span className="sr-only"> (طی شده)</span>}
              </li>
            ))}
          </ol>

          <div className="meta-grid">
            <div><span>وضعیت</span><Badge kind="st" value={alert.status} labels={STATUS_LABELS} /></div>
            <div><span>شدت</span><Badge kind="sev" value={alert.severity} labels={SEVERITY_LABELS} /></div>
            <div><span>مالک</span><strong dir="ltr">{alert.assigned_to || 'بدون مالک'}</strong></div>
            <div><span>مشتری</span><strong>{alert.customer_detail ? `${alert.customer_detail.first_name} ${alert.customer_detail.last_name}` : '—'}</strong></div>
            <div><span>باز شده</span><strong>{fmtDate(alert.created_at)}</strong></div>
            <div><span>نتیجه</span><strong>{OUTCOMES.includes(alert.status) ? STATUS_LABELS[alert.status] : 'در جریان'}</strong></div>
          </div>

          <section className="block-section">
            <h3>تصمیم‌ها</h3>
            {history === null ? <p className="muted" role="status">در حال بارگذاری…</p>
              : decisions.length === 0 ? <p className="muted">تصمیمی ثبت نشده است.</p>
              : <ul className="timeline">{decisions.map((item) => (
                <li key={item.id} className="tl-STATUS_CHANGE">
                  <div className="tl-head"><span className="tl-type">تصمیم</span><span dir="ltr">{item.author}</span><time>{fmtDate(item.created_at)}</time></div>
                  <p>{item.comment || 'بدون توضیح'}</p>
                </li>
              ))}</ul>}
          </section>

          {(canReview || canAssign) && !OUTCOMES.includes(alert.status) && (
            <section className="block-section">
              <h3>اقدام بعدی</h3>
              <div className="stack">
                <div className="field">
                  <label htmlFor="case-notes">دلیل یا یادداشت اقدام{REQUIRED_NOTE.includes(drafter.status) ? ' (الزامی)' : ''}</label>
                  <textarea id="case-notes" rows={3} value={drafter.notes} onChange={(event) => setDrafter({ ...drafter, notes: event.target.value })} />
                </div>
                <div className="row-gap">
                  {canReview && <Button disabled={busy} onClick={() => save('UNDER_REVIEW')}>در حال بررسی</Button>}
                  {canAssign && <Button variant="danger" disabled={busy} onClick={async () => { setBusy(true); try { onChanged(await api.review(alert.alert_id, 'ESCALATED', drafter.notes)); setDrafter((d) => ({ ...d, notes: '' })); } catch (err) { setError(err.message); } finally { setBusy(false); } }}>ارجاع سطح بالا ({STATUS_LABELS.ESCALATED})</Button>}
                  {canReview && <Button variant="primary" disabled={busy} onClick={() => save('RESOLVED')}>حل‌شده ({STATUS_LABELS.RESOLVED})</Button>}
                  {canReview && <Button disabled={busy} onClick={() => save('FALSE_POSITIVE')}>مثبت کاذب ({STATUS_LABELS.FALSE_POSITIVE})</Button>}
                </div>
                {!canReview && canAssign && <p className="muted">ثبت نتیجهٔ نهایی با بررسی‌کنندهٔ مالک پرونده است؛ شما می‌توانید پرونده را ارتقا دهید تا مالک آن را نهایی کند.</p>}
              </div>
            </section>
          )}

          {OUTCOMES.includes(alert.status) && (
            <section className="block-section">
              <h3>پرونده بسته شده است</h3>
              <p className="muted">نتیجهٔ «{STATUS_LABELS[alert.status]}» ثبت شده و در تاریخچهٔ پرونده و گزارش ممیزی قابل ردیابی است. برای بازبینی دوباره، هشدار را از صف عملیات بررسی کنید.</p>
            </section>
          )}
        </div>
      </aside>
    </div>
  );
}
