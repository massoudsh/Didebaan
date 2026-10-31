import { useCallback, useEffect, useRef, useState } from 'react';
import { api } from '../api.js';
import {
  COMMENT_TYPE_LABELS, fmtAge, fmtAmount, fmtDate, fmtScore,
  REVIEW_STATUSES, SEVERITY_LABELS, STATUS_LABELS,
} from '../format.js';
import { Badge, Button, IconButton, InlineNotice } from './ui.jsx';

const CONSEQUENTIAL = ['RESOLVED', 'FALSE_POSITIVE', 'ESCALATED'];
const REQUIRED_NOTE = ['RESOLVED', 'FALSE_POSITIVE'];

export default function AlertDetail({ alert, currentUser, canAssign, canReview, onClose, onChanged, onOpenEntity, onOpenAlert }) {
  const id = alert.alert_id;
  const [comments, setComments] = useState([]);
  const [related, setRelated] = useState(null);
  const [loadingComments, setLoadingComments] = useState(true);
  const [assignee, setAssignee] = useState(alert.assigned_to || '');
  const [assignNotes, setAssignNotes] = useState('');
  const [reviewStatus, setReviewStatus] = useState('UNDER_REVIEW');
  const [reviewNotes, setReviewNotes] = useState('');
  const [confirmReview, setConfirmReview] = useState(false);
  const [newComment, setNewComment] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const drawer = useRef(null);
  const noteField = useRef(null);

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
    let active = true;
    setRelated(null);
    api.relatedAlerts(id)
      .then((data) => active && setRelated(data))
      .catch(() => active && setRelated({ results: [], unavailable: true }));
    return () => { active = false; };
  }, [id]);

  useEffect(() => {
    const previous = document.activeElement;
    const node = drawer.current;
    node?.querySelector('button')?.focus();
    const onKey = (event) => {
      if (event.key === 'Escape') {
        onClose();
        return;
      }
      if (event.key !== 'Tab' || !node) return;
      const focusable = [...node.querySelectorAll('button, input, textarea, select, a[href], [tabindex]:not([tabindex="-1"])')]
        .filter((item) => !item.disabled);
      if (!focusable.length) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    };
    document.addEventListener('keydown', onKey);
    document.body.style.overflow = 'hidden';
    return () => {
      document.removeEventListener('keydown', onKey);
      document.body.style.overflow = '';
      previous?.focus?.({ preventScroll: true });
    };
  }, [onClose]);

  async function run(task, success) {
    setBusy(true);
    setError('');
    try {
      await task();
      if (success) setNotice(success);
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
    }, 'ارجاع ثبت شد و در تاریخچهٔ پرونده درج گردید.');
  };

  const submitReview = (event) => {
    event.preventDefault();
    if (CONSEQUENTIAL.includes(reviewStatus) && !confirmReview) {
      setConfirmReview(true);
      noteField.current?.focus();
      return;
    }
    if (REQUIRED_NOTE.includes(reviewStatus) && !reviewNotes.trim()) {
      setError('برای نتیجهٔ نهایی، دلیل تصمیم را در یادداشت بازبینی بنویسید.');
      noteField.current?.focus();
      return;
    }
    run(async () => {
      await api.review(id, reviewStatus, reviewNotes);
      setReviewNotes('');
      setConfirmReview(false);
      await refresh();
    }, 'تصمیم ثبت شد و در تاریخچه و گزارش ممیزی نگهداری می‌شود.');
  };

  const submitComment = (event) => {
    event.preventDefault();
    if (!newComment.trim()) return;
    run(async () => {
      await api.addComment(id, newComment.trim());
      setNewComment('');
      await loadComments();
    }, 'یادداشت به تاریخچه افزوده شد.');
  };

  const exportHistory = () => run(() => api.exportComments({ export_format: 'csv', alert_id: id }), 'خروجی CSV تاریخچه آماده شد.');
  const exportBundle = () => run(() => api.exportCase(id), 'بستهٔ شواهد JSON برای دانلود ارسال شد.');

  const txn = alert.transaction_detail;
  const customer = alert.customer_detail;
  const device = txn?.device_detail;
  const merchant = txn?.merchant_detail;
  const explanation = Array.isArray(alert.explanation) ? alert.explanation : [];
  const flagged = Array.isArray(txn?.flagged_reasons) ? txn.flagged_reasons.filter((item) => typeof item === 'string' && item.trim()) : [];

  return (
    <div className="drawer-backdrop" onClick={onClose}>
      <aside ref={drawer} className="drawer" role="dialog" aria-modal="true" aria-labelledby="alert-detail-title" onClick={(e) => e.stopPropagation()}>
        <header className="drawer-head">
          <div>
            <h2 id="alert-detail-title" dir="ltr" className="mono">{id}</h2>
            <p>{alert.title}</p>
          </div>
          <IconButton label="بستن" onClick={onClose}>✕</IconButton>
        </header>

        <div className="drawer-body">
          {error && <p className="error" role="alert">{error}</p>}
          {notice && <p className="notice" role="status">{notice}</p>}

          <div className="meta-grid">
            <div><span>شدت</span><Badge kind="sev" value={alert.severity} labels={SEVERITY_LABELS} /></div>
            <div><span>وضعیت</span><Badge kind="st" value={alert.status} labels={STATUS_LABELS} /></div>
            <div><span>امتیاز ریسک</span><strong>{fmtScore(alert.risk_score)}</strong></div>
            <div><span>زمان ثبت</span><strong>{fmtDate(alert.created_at)}</strong></div>
            <div>
              <span>مشتری</span>
              {customer ? (
                <button className="link name-link" onClick={() => onOpenEntity?.({ kind: 'customer', id: customer.customer_id, label: customer.customer_id })}>
                  {customer.first_name} {customer.last_name}
                </button>
              ) : <strong>—</strong>}
            </div>
            <div><span>تراکنش</span><strong>{txn ? fmtAmount(txn.amount, txn.currency) : '—'}</strong></div>
            <div>
              <span>بررسی‌کننده</span>
              <strong dir="ltr">{alert.assigned_to || '—'}</strong>
              {alert.assigned_to && <small className="muted block">از {fmtAge(alert.assigned_at)} پیش</small>}
            </div>
            <div><span>آخرین بازبینی</span><strong>{alert.reviewed_by ? `${alert.reviewed_by} · ${fmtDate(alert.reviewed_at)}` : '—'}</strong></div>
          </div>

          {(device || merchant) && (
            <section className="block-section">
              <h3>موجودیت‌های مرتبط</h3>
              <div className="row-gap">
                {device && <button className="chip chip-btn" onClick={() => onOpenEntity?.({ kind: 'device', id: device.device_id, label: device.device_id })}>دستگاه <span className="mono" dir="ltr">{device.device_id}</span></button>}
                {merchant && <button className="chip chip-btn" onClick={() => onOpenEntity?.({ kind: 'merchant', id: merchant.merchant_id, label: merchant.name || merchant.merchant_id })}>پذیرنده <span dir="ltr">{merchant.name || merchant.merchant_id}</span></button>}
                {customer && <button className="chip chip-btn" onClick={() => onOpenEntity?.({ kind: 'customer', id: customer.customer_id, label: customer.customer_id })}>مشتری <span className="mono" dir="ltr">{customer.customer_id}</span></button>}
              </div>
              {device && (device.is_emulator || device.is_rooted) && (
                <InlineNotice tone="warn">نشانهٔ دستگاه مشکوک: {device.is_emulator ? 'شبیه‌ساز' : ''}{device.is_emulator && device.is_rooted ? ' · ' : ''}{device.is_rooted ? 'دستکاری‌شده' : ''}. این تنها یک سرنخ است، نه اثبات تقلب.</InlineNotice>
              )}
            </section>
          )}

          {explanation.length > 0 && (
            <section className="block-section">
              <h3>چرا این هشدار ثبت شد؟</h3>
              <ul className="explain">
                {explanation.map((item, index) => (
                  <li key={index}>
                    <strong>{item.rule_name || 'قانون'}</strong>
                    <span>{item.reason}</span>
                    {item.weight !== undefined && <em>وزن قانون: {fmtScore(item.weight)}</em>}
                  </li>
                ))}
              </ul>
            </section>
          )}

          {flagged.length > 0 && (
            <section className="block-section">
              <h3>سرنخ‌های ثبت‌شده تراکنش</h3>
              <ul className="explain">
                {flagged.map((item, index) => <li key={index}><span>{item}</span></li>)}
              </ul>
            </section>
          )}

          <section className="block-section">
            <h3>هشدارهای مرتبط همین مشتری</h3>
            {related === null && <p className="muted" role="status">در حال بارگذاری…</p>}
            {related?.unavailable && <p className="muted">فهرست هشدارهای مرتبط در دسترس نیست؛ سایر بخش‌های پرونده قابل استفاده است.</p>}
            {related && !related.unavailable && related.results.length === 0 && <p className="muted">هشدار دیگری برای این مشتری ثبت نشده است.</p>}
            {related?.results?.length > 0 && (
              <div className="table-wrap">
                <table className="intelligence-table">
                  <thead><tr><th>شناسه</th><th>شدت</th><th>وضعیت</th><th>زمان</th></tr></thead>
                  <tbody>
                    {related.results.map((item) => (
                      <tr key={item.alert_id} className="clickable" onClick={() => onOpenAlert?.(item.alert_id)} tabIndex={0} onKeyDown={(event) => event.key === 'Enter' && onOpenAlert?.(item.alert_id)}>
                        <td className="mono">{item.alert_id}</td>
                        <td><Badge kind="sev" value={item.severity} labels={SEVERITY_LABELS} /></td>
                        <td><Badge kind="st" value={item.status} labels={STATUS_LABELS} /></td>
                        <td>{fmtDate(item.created_at)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          {canAssign && <section className="block-section">
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
                <Button onClick={() => setAssignee(currentUser)}>خودم</Button>
              </div>
              <input value={assignNotes} onChange={(e) => setAssignNotes(e.target.value)} placeholder="توضیح ارجاع (اختیاری)" aria-label="توضیح ارجاع" />
              <Button variant="primary" type="submit" loading={busy}>ثبت ارجاع</Button>
            </form>
          </section>}

          {canReview && <section className="block-section">
            <h3>بازبینی و تصمیم</h3>
            <form className="stack" onSubmit={submitReview}>
              <div className="field">
                <label htmlFor="review-status">وضعیت جدید</label>
                <select id="review-status" value={reviewStatus} onChange={(e) => { setReviewStatus(e.target.value); setConfirmReview(false); }}>
                  {REVIEW_STATUSES.map((value) => <option key={value} value={value}>{STATUS_LABELS[value]}</option>)}
                </select>
              </div>
              <div className="field">
                <label htmlFor="review-notes">یادداشت بازبینی{REQUIRED_NOTE.includes(reviewStatus) ? ' (الزامی برای نتیجهٔ نهایی)' : ''}</label>
                <textarea ref={noteField} id="review-notes" value={reviewNotes} onChange={(e) => setReviewNotes(e.target.value)} rows={2} aria-required={REQUIRED_NOTE.includes(reviewStatus)} />
              </div>
              {confirmReview && (
                <div className="confirm-box" role="alertdialog" aria-label="تأیید تصمیم نهایی">
                  <p>ثبت وضعیت «{STATUS_LABELS[reviewStatus]}» تصمیم نهایی پرونده است و در گزارش ممیزی ثبت می‌شود. ادامه می‌دهید؟</p>
                  <div className="row-gap">
                    <Button variant="primary" type="submit" loading={busy}>تأیید ثبت تصمیم</Button>
                    <Button variant="ghost" onClick={() => setConfirmReview(false)}>بازگشت</Button>
                  </div>
                </div>
              )}
              {!confirmReview && <Button variant="primary" type="submit" loading={busy}>ثبت تصمیم</Button>}
            </form>
          </section>}

          <section className="block-section">
            <div className="section-head">
              <h3>تاریخچهٔ پرونده</h3>
              <div className="row-gap">
                <Button onClick={exportHistory} disabled={busy} loading={busy}>خروجی CSV</Button>
                <Button onClick={exportBundle} disabled={busy}>بستهٔ شواهد JSON</Button>
              </div>
            </div>
            {canReview && <form className="stack" onSubmit={submitComment}>
              <textarea value={newComment} onChange={(e) => setNewComment(e.target.value)} placeholder="یادداشت تازهٔ بررسی…" rows={2} aria-label="یادداشت تازه" />
              <Button type="submit" disabled={busy || !newComment.trim()}>افزودن یادداشت</Button>
            </form>}
            {loadingComments ? (
              <p className="muted" role="status">در حال بارگذاری…</p>
            ) : comments.length === 0 ? (
              <p className="muted">هنوز موردی ثبت نشده است.</p>
            ) : (
              <ol className="timeline" aria-label="تاریخچهٔ پرونده">
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
