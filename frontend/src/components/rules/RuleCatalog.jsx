import { useCallback, useEffect, useMemo, useState } from 'react';
import { api } from '../../api.js';
import { fmtDate, fmtNumber } from '../../format.js';
import { Button, ConfirmBar, EmptyState, ErrorState, InlineNotice, TableSkeleton } from '../ui.jsx';

export const RULE_TYPES = {
  THRESHOLD: { label: 'آستانه', plain: 'فعال‌سازی وقتی مبلغ یا تعداد در بازه از حد تعیین‌شده بگذرد.' },
  PATTERN: { label: 'الگو', plain: 'شناسایی الگوهای شکستن مبلغ یا تراکنش‌های پرشمار و سریع.' },
  BEHAVIORAL: { label: 'رفتاری', plain: 'نقض الگوی عادی مشتری در مبلغ یا رفتار تراکنش.' },
  GEOGRAPHIC: { label: 'جغرافیایی', plain: 'تراکنش با کشور پرخطر یا عبور از مرز.' },
  PEP: { label: 'PEP', plain: 'بررسی مشتریان دارای سمت سیاسی یا عمومی.' },
  VELOCITY: { label: 'سرعت تراکنش', plain: 'تعداد بالای تراکنش در بازهٔ کوتاه.' },
  CONCENTRATION: { label: 'تمرکز', plain: 'تمرکز تراکنش‌ها روی یک دریافت‌کننده.' },
  SANCTIONED: { label: 'کشور تحریمی', plain: 'تراکنش با کشورهای فهرست پایش تحریمی.' },
  NIGHT_WEEKEND: { label: 'شبانه/تعطیل', plain: 'فعالیت در ساعات غیرمتعارف.' },
  ROUND_AMOUNT: { label: 'مبلغ رُند', plain: 'الگوی مبالغ رُند یا شکستن تراکنش.' },
  NEW_ACCOUNT: { label: 'حساب تازه', plain: 'فعالیت زیاد در حساب‌های کم‌عمر.' },
  DEVICE_SHARING: { label: 'اشتراک دستگاه', plain: 'یک دستگاه میان چند حساب.' },
  MERCHANT_ABUSE: { label: 'سوءاستفادهٔ پذیرنده', plain: 'خرید ساختگی یا شارژبک غیرعادی پذیرنده.' },
  BNPL_RISK: { label: 'ریسک BNPL', plain: 'الگوی ریسک نکول خرید اعتباری.' },
};

const STATUS_LABELS = { ACTIVE: 'فعال', INACTIVE: 'غیرفعال', DRAFT: 'پیش‌نویس' };
const STATUS_TONE = { ACTIVE: 'ok', INACTIVE: 'muted', DRAFT: 'warn' };
const SENSITIVE_KEYS = /secret|token|password|key|credential|pepper|salt/i;

export function describeRuleConfiguration(ruleType, configuration) {
  if (!configuration || typeof configuration !== 'object') return [];
  return Object.entries(configuration).map(([key, value]) => {
    const sensitive = SENSITIVE_KEYS.test(key);
    return {
      key,
      label: key,
      value: sensitive ? 'مقدار محرمانه — نمایش داده نمی‌شود' : typeof value === 'object' ? JSON.stringify(value) : String(value),
      sensitive,
    };
  });
}

export function ruleChangeSummary(previous, next) {
  if (!previous || !next) return [];
  const keys = new Set([...Object.keys(previous), ...Object.keys(next)]);
  return [...keys]
    .filter((key) => !SENSITIVE_KEYS.test(key) && JSON.stringify(previous[key]) !== JSON.stringify(next[key]))
    .map((key) => ({ key, before: previous[key], after: next[key] }));
}

export default function RuleCatalog({ roles = [] }) {
  const editable = roles.includes('COMPLIANCE_OFFICER');
  const readOnlyTypes = Object.keys(RULE_TYPES).filter((type) => !['THRESHOLD', 'PATTERN', 'BEHAVIORAL', 'GEOGRAPHIC'].includes(type));
  const [type, setType] = useState('');
  const [status, setStatus] = useState('');
  const [rules, setRules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selected, setSelected] = useState(null);
  const [draft, setDraft] = useState('');
  const [draftError, setDraftError] = useState('');
  const [pending, setPending] = useState(false);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const first = await api.rules({ rule_type: type, status, page_size: 100 });
      let results = first.results;
      if (first.next) {
        const second = await api.rules({ rule_type: type, status, page_size: 100, page: 2 });
        results = [...results, ...second.results];
      }
      setRules(results);
      setError('');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [type, status]);

  useEffect(() => { load(); }, [load]);

  function choose(rule) {
    setSelected(rule);
    setDraft(JSON.stringify(rule.configuration ?? {}, null, 2));
    setDraftError('');
    setPending(false);
    setNotice('');
  }

  const changes = useMemo(() => {
    if (!selected) return [];
    try {
      return ruleChangeSummary(selected.configuration, JSON.parse(draft));
    } catch {
      return [];
    }
  }, [selected, draft]);

  async function submitChange(action) {
    if (!selected) return;
    let configuration;
    try {
      configuration = JSON.parse(draft);
    } catch {
      setDraftError('تنظیمات باید JSON معتبر باشد.');
      return;
    }
    if (!configuration || typeof configuration !== 'object' || Array.isArray(configuration)) {
      setDraftError('تنظیمات باید یک شیء JSON باشد.');
      return;
    }
    setBusy(true);
    setDraftError('');
    try {
      const payload = { configuration };
      if (action === 'activate' || action === 'deactivate') payload.status = action === 'activate' ? 'ACTIVE' : 'INACTIVE';
      const updated = await api.updateRule(selected.id, payload);
      setSelected(updated);
      setDraft(JSON.stringify(updated.configuration ?? {}, null, 2));
      setPending(false);
      setNotice(action === 'activate' ? 'قانون فعال شد؛ تغییر در گزارش ممیزی ثبت می‌شود.' : action === 'deactivate' ? 'قانون غیرفعال شد.' : 'تنظیمات قانون به‌روزرسانی شد.');
      load();
    } catch (err) {
      setDraftError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section>
      <div className="page-head">
        <div>
          <h2>قوانین، سیگنال‌ها و شفافیت</h2>
          <p className="muted">
            {editable
              ? 'تغییر تنظیمات و وضعیت قانون با ثبت تاریخچهٔ ممیزی انجام می‌شود؛ برای سنجش اثر ابتدا در «آزمایش قوانین» شبیه‌سازی کنید.'
              : 'شما فقط می‌توانید قوانین را مشاهده کنید؛ تغییرات به افسر انطباق وابسته است.'}
          </p>
        </div>
        <Button onClick={load} loading={loading}>تازه‌سازی</Button>
      </div>

      <div className="filters card" style={{ gridTemplateColumns: 'repeat(2, minmax(0, 1fr))' }}>
        <div className="field">
          <label htmlFor="rule-type">نوع قانون یا سیگنال</label>
          <select id="rule-type" value={type} onChange={(event) => setType(event.target.value)}>
            <option value="">همه</option>
            {Object.entries(RULE_TYPES).map(([value, meta]) => <option key={value} value={value}>{meta.label}</option>)}
          </select>
        </div>
        <div className="field">
          <label htmlFor="rule-status">وضعیت</label>
          <select id="rule-status" value={status} onChange={(event) => setStatus(event.target.value)}>
            <option value="">همه</option>
            {Object.entries(STATUS_LABELS).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
          </select>
        </div>
      </div>

      {notice && <p className="notice" role="status">{notice}</p>}
      {error && <ErrorState message={error} onRetry={load} />}

      <div className="grid-2" style={{ gridTemplateColumns: 'minmax(280px, 1fr) minmax(320px, 1.4fr)', alignItems: 'start' }}>
        <div className="card" style={{ overflow: 'hidden' }}>
          {loading && !rules.length ? <TableSkeleton rows={5} columns={3} /> : rules.length === 0 ? (
            <EmptyState title="قانونی مطابق فیلتر نیست">با تغییر نوع یا وضعیت دوباره بررسی کنید.</EmptyState>
          ) : (
            <ul className="rule-list" aria-label="فهرست قوانین">
              {rules.map((rule) => (
                <li key={rule.id}>
                  <button type="button" className={`rule-item${selected?.id === rule.id ? ' active' : ''}`} aria-pressed={selected?.id === rule.id} onClick={() => choose(rule)}>
                    <span className="rule-item-head">
                      <strong>{rule.name}</strong>
                      <span className={`badge ${STATUS_TONE[rule.status] === 'ok' ? 'st-RESOLVED' : STATUS_TONE[rule.status] === 'warn' ? 'st-UNDER_REVIEW' : 'st-FALSE_POSITIVE'}`}>{STATUS_LABELS[rule.status] || rule.status}</span>
                    </span>
                    <small className="muted">{RULE_TYPES[rule.rule_type]?.label || rule.rule_type} · وزن {fmtNumber(rule.risk_weight)}</small>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="card panel">
          {!selected ? <EmptyState title="یک قانون انتخاب کنید">جزئیات، پارامترها و شفافیت هر قانون را اینجا می‌بینید.</EmptyState> : (
            <>
              <div className="panel-head">
                <h3>{selected.name}</h3>
                <span className="badge st-FALSE_POSITIVE">{STATUS_LABELS[selected.status] || selected.status}</span>
              </div>
              <p>{RULE_TYPES[selected.rule_type]?.plain || 'توضیح عمومی این نوع قانون ثبت نشده است.'}</p>
              <div className="meta-grid" style={{ marginBottom: '1rem' }}>
                <div><span>نوع</span><strong>{RULE_TYPES[selected.rule_type]?.label || selected.rule_type}</strong></div>
                <div><span>وزن ریسک</span><strong>{fmtNumber(selected.risk_weight)}</strong></div>
                <div><span>اولویت</span><strong>{fmtNumber(selected.priority)}</strong></div>
                <div><span>آخرین به‌روزرسانی</span><strong>{fmtDate(selected.updated_at)}</strong></div>
                <div><span>آخرین اجرا</span><strong>{fmtDate(selected.last_applied_at)}</strong></div>
                <div><span>سازنده</span><strong dir="ltr">{selected.created_by || '—'}</strong></div>
              </div>
              {selected.description && <p className="muted">{selected.description}</p>}

              <h3>پارامترهای فعلی</h3>
              <div className="table-wrap">
                <table className="intelligence-table">
                  <thead><tr><th>پارامتر</th><th>مقدار</th></tr></thead>
                  <tbody>
                    {describeRuleConfiguration(selected.rule_type, selected.configuration).map((item) => (
                      <tr key={item.key}><td className="mono">{item.label}</td><td>{item.value}</td></tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {readOnlyTypes.includes(selected.rule_type) && <InlineNotice tone="warn">این نوع قانون از شبیه‌سازی چهار‌گانه پشتیبانی نمی‌کند؛ تغییر پارامتر باید با بررسی انسانی و تأیید انطباق انجام شود.</InlineNotice>}

              {editable ? (
                <section className="block-section" style={{ marginTop: '1rem' }}>
                  <h3>ویرایش تنظیمات (JSON)</h3>
                  <div className="field">
                    <label htmlFor="rule-config">تنظیمات پیشنهادی</label>
                    <textarea id="rule-config" dir="ltr" rows={7} value={draft} onChange={(event) => { setDraft(event.target.value); setPending(false); }} aria-describedby="rule-config-hint" aria-invalid={draftError ? true : undefined} />
                    <small id="rule-config-hint" className="field-hint">فقط پارامترهای تشخیصی این نوع قانون را تغییر دهید. تغییرات قبل از ثبت، خلاصه و تأیید می‌شود.</small>
                  </div>
                  {draftError && <p className="error" role="alert">{draftError}</p>}
                  {changes.length > 0 && (
                    <div className="table-wrap" style={{ margin: '.8rem 0' }}>
                      <table className="intelligence-table">
                        <thead><tr><th>پارامتر</th><th>قبل</th><th>بعد</th></tr></thead>
                        <tbody>{changes.map((change) => <tr key={change.key}><td className="mono">{change.key}</td><td>{String(change.before ?? '—')}</td><td>{String(change.after ?? '—')}</td></tr>)}</tbody>
                      </table>
                    </div>
                  )}
                  {pending ? (
                    <ConfirmBar
                      message={pending === 'activate' ? 'با فعال‌سازی، این قانون روی تراکنش‌های تازه اجرا می‌شود. ادامه می‌دهید؟' : pending === 'deactivate' ? 'با غیرفعال‌سازی، این قانون دیگر هشدار تولید نمی‌کند. ادامه می‌دهید؟' : `تغییر ${fmtNumber(changes.length)} پارامتر در گزارش ممیزی ثبت می‌شود. ادامه می‌دهید؟`}
                      confirmLabel="تأیید و ثبت تغییر"
                      busy={busy}
                      onConfirm={() => submitChange(pending)}
                      onCancel={() => setPending(false)}
                    />
                  ) : (
                    <div className="row-gap">
                      <Button variant="primary" disabled={!changes.length} onClick={() => setPending('save')}>ثبت تنظیمات</Button>
                      {selected.status === 'ACTIVE'
                        ? <Button variant="danger" onClick={() => setPending('deactivate')}>غیرفعال‌سازی</Button>
                        : <Button onClick={() => setPending('activate')}>فعال‌سازی</Button>}
                    </div>
                  )}
                </section>
              ) : (
                <p className="muted">برای تغییر تنظیمات، افسر انطباق باید از این صفحه اقدام کند.</p>
              )}
            </>
          )}
        </div>
      </div>
    </section>
  );
}
