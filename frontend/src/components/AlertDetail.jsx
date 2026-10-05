import { useCallback, useEffect, useState } from 'react';
import { api } from '../api.js';
import {
  COMMENT_TYPE_LABELS, fmtAge, fmtAmount, fmtDate, fmtScore,
  REVIEW_STATUSES, SEVERITY_LABELS, STATUS_LABELS,
} from '../format.js';
import { Badge } from './AlertQueue.jsx';

export default function AlertDetail({ alert, currentUser, onClose, onChanged }) {
  const id = alert.alert_id;
  const [comments, setComments] = useState([]);
  const [loadingComments, setLoadingComments] = useState(true);
  const [assignee, setAssignee] = useState(alert.assigned_to || '');
  const [assignNotes, setAssignNotes] = useState('');
  const [reviewStatus, setReviewStatus] = useState('UNDER_REVIEW');
  const [reviewNotes, setReviewNotes] = useState('');
  const [newComment, setNewComment] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  const loadComments = useCallback(async () => {
    try {
      setComments(await api.comments(id));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoadingComments(false);
    }
  }, [id]);

  useEffect(() => {
    loadComments();
  }, [loadComments]);

  useEffect(() => {
    const onKey = (event) => event.key === 'Escape' && onClose();
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onClose]);

  async function run(task) {
    setBusy(true);
    setError('');
    try {
      await task();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  const refresh = async () => {
    onChanged(await api.alert(id));
    await loadComments();
  };

  const submitAssign = (event) => {
    event.preventDefault();
    run(async () => {
      await api.assign(id, assignee.trim(), assignNotes);
      setAssignNotes('');
      await refresh();
    });
  };

  const submitReview = (event) => {
    event.preventDefault();
    run(async () => {
      await api.review(id, reviewStatus, reviewNotes);
      setReviewNotes('');
      await refresh();
    });
  };

  const submitComment = (event) => {
    event.preventDefault();
    if (!newComment.trim()) return;
    run(async () => {
      await api.addComment(id, newComment.trim());
      setNewComment('');
      await loadComments();
    });
  };

  const exportHistory = () => run(() => api.exportComments({ export_format: 'csv', alert_id: id }));

  const txn = alert.transaction_detail;
  const customer = alert.customer_detail;
  const explanation = Array.isArray(alert.explanation) ? alert.explanation : [];

  return (
    <div className="drawer-backdrop" onClick={onClose}>
      <aside className="drawer" role="dialog" aria-modal="true" aria-label={`جزئیات هشدار ${id}`} onClick={(e) => e.stopPropagation()}>
        <header className="drawer-head">
          <div>
            <h2 dir="ltr" className="mono">{id}</h2>
            <p>{alert.title}</p>
          </div>
          <button className="btn ghost" onClick={onClose} aria-label="بستن">✕</button>
        </header>

        <div className="drawer-body">
          {error && <p className="error" role="alert">{error}</p>}

          <div className="meta-grid">
            <div><span>شدت</span><Badge kind="sev" value={alert.severity} labels={SEVERITY_LABELS} /></div>
            <div><span>وضعیت</span><Badge kind="st" value={alert.status} labels={STATUS_LABELS} /></div>
            <div><span>امتیاز ریسک</span><strong>{fmtScore(alert.risk_score)}</strong></div>
            <div><span>زمان ثبت</span><strong>{fmtDate(alert.created_at)}</strong></div>
            <div><span>مشتری</span><strong>{customer ? `${customer.first_name} ${customer.last_name}` : '—'}</strong></div>
            <div><span>تراکنش</span><strong>{txn ? fmtAmount(txn.amount, txn.currency) : '—'}</strong></div>
            <div>
              <span>بررسی‌کننده</span>
              <strong dir="ltr">{alert.assigned_to || '—'}</strong>
              {alert.assigned_to && <small className="muted block">از {fmtAge(alert.assigned_at)} پیش</small>}
            </div>
            <div><span>آخرین بازبینی</span><strong>{alert.reviewed_by ? `${alert.reviewed_by} · ${fmtDate(alert.reviewed_at)}` : '—'}</strong></div>
          </div>

          {explanation.length > 0 && (
            <section className="block-section">
              <h3>چرا این هشدار ثبت شد؟</h3>
              <ul className="explain">
                {explanation.map((item, index) => (
                  <li key={index}>
                    <strong>{item.rule || 'قانون'}</strong>
                    <span>{item.reason}</span>
                    {item.contribution !== undefined && <em>سهم: {fmtScore(item.contribution)}</em>}
                  </li>
                ))}
              </ul>
            </section>
          )}

          <section className="block-section">
            <h3>ارجاع</h3>
            <form className="stack" onSubmit={submitAssign}>
              <div className="row-gap">
                <input
                  className="grow"
                  value={assignee}
                  onChange={(e) => setAssignee(e.target.value)}
                  placeholder="نام کاربری بررسی‌کننده (خالی = لغو ارجاع)"
                  dir="ltr"
                  aria-label="نام کاربری بررسی‌کننده"
                />
                <button type="button" className="btn" onClick={() => setAssignee(currentUser)}>خودم</button>
              </div>
              <input value={assignNotes} onChange={(e) => setAssignNotes(e.target.value)} placeholder="توضیح ارجاع (اختیاری)" aria-label="توضیح ارجاع" />
              <button className="btn primary" disabled={busy}>ثبت ارجاع</button>
            </form>
          </section>

          <section className="block-section">
            <h3>بازبینی و تصمیم</h3>
            <form className="stack" onSubmit={submitReview}>
              <select value={reviewStatus} onChange={(e) => setReviewStatus(e.target.value)} aria-label="وضعیت جدید">
                {REVIEW_STATUSES.map((value) => <option key={value} value={value}>{STATUS_LABELS[value]}</option>)}
              </select>
              <textarea value={reviewNotes} onChange={(e) => setReviewNotes(e.target.value)} placeholder="یادداشت بازبینی" rows={2} aria-label="یادداشت بازبینی" />
              <button className="btn primary" disabled={busy}>ثبت تصمیم</button>
            </form>
          </section>

          <section className="block-section">
            <div className="section-head">
              <h3>تاریخچهٔ پرونده</h3>
              <button className="btn" onClick={exportHistory} disabled={busy}>خروجی CSV</button>
            </div>
            <form className="stack" onSubmit={submitComment}>
              <textarea value={newComment} onChange={(e) => setNewComment(e.target.value)} placeholder="یادداشت تازهٔ بررسی…" rows={2} aria-label="یادداشت تازه" />
              <button className="btn" disabled={busy || !newComment.trim()}>افزودن یادداشت</button>
            </form>
            {loadingComments ? (
              <p className="muted">در حال بارگذاری…</p>
            ) : comments.length === 0 ? (
              <p className="muted">هنوز موردی ثبت نشده است.</p>
            ) : (
              <ol className="timeline">
                {comments.map((item) => (
                  <li key={item.id} className={`tl-${item.comment_type}`}>
                    <div className="tl-head">
                      <span className="tl-type">{COMMENT_TYPE_LABELS[item.comment_type] || item.comment_type}</span>
                      <span dir="ltr">{item.author}</span>
                      <time>{fmtDate(item.created_at)}</time>
                    </div>
                    <p>{item.comment}</p>
                  </li>
                ))}
              </ol>
            )}
          </section>
        </div>
      </aside>
    </div>
  );
}
