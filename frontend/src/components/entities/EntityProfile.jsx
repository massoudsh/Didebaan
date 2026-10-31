import { useCallback, useEffect, useState } from 'react';
import { api } from '../../api.js';
import { fmtAmount, fmtDate, fmtNumber, fmtScore, SEVERITY_LABELS, STATUS_LABELS } from '../../format.js';
import { Badge, Button, ErrorState, InlineNotice, TableSkeleton } from '../ui.jsx';

const KIND_LABELS = { customer: 'مشتری / نهاد', device: 'دستگاه', merchant: 'پذیرنده' };

export function maskNationalId(value, roles) {
  if (!value) return '—';
  if (roles.includes('COMPLIANCE_OFFICER')) return value;
  const digits = String(value);
  return `${digits.slice(0, 3)}${'•'.repeat(Math.max(0, digits.length - 6))}${digits.slice(-3)}`;
}

export function maskEmail(value, roles) {
  if (!value) return '—';
  if (roles.includes('COMPLIANCE_OFFICER')) return value;
  const [local, domain] = String(value).split('@');
  return domain ? `${local.slice(0, 1)}•••@${domain}` : '•••';
}

export default function EntityProfile({ entity, roles = [], onBack, onOpenAlert }) {
  const [state, setState] = useState({ loading: true, data: null, error: '' });

  const load = useCallback(async () => {
    setState({ loading: true, data: null, error: '' });
    try {
      const data = entity.kind === 'customer'
        ? await loadCustomer(entity.id)
        : entity.kind === 'device'
          ? await loadDevice(entity.id)
          : await loadMerchant(entity.id);
      setState({ loading: false, data, error: '' });
    } catch (err) {
      setState({ loading: false, data: null, error: err.status === 404 ? 'این موجودیت در سامانه پیدا نشد.' : err.message });
    }
  }, [entity.kind, entity.id]);

  useEffect(() => { load(); }, [load]);

  if (state.loading) return <section><p className="muted pad" role="status">در حال بارگذاری پروفایل…</p><TableSkeleton rows={4} columns={4} /></section>;
  if (state.error) return <section><Button onClick={onBack}>بازگشت</Button><ErrorState message={state.error} onRetry={load} /></section>;

  const { data } = state;
  return (
    <section>
      <div className="page-head">
        <div>
          <span className="eyebrow accent">{KIND_LABELS[entity.kind]}</span>
          <h2 className="mono" dir="ltr">{data.header.id}</h2>
          <p className="muted">{data.header.title}</p>
        </div>
        <Button onClick={onBack}>بازگشت</Button>
      </div>

      <div className="kpi-grid">
        {data.header.kpis.map((kpi) => (
          <div className="kpi" key={kpi.label}><span>{kpi.label}</span><strong>{kpi.value}</strong>{kpi.hint && <small>{kpi.hint}</small>}</div>
        ))}
      </div>

      {data.notice && <InlineNotice tone="warn">{data.notice}</InlineNotice>}

      {entity.kind === 'customer' && <CustomerSections data={data} roles={roles} />}

      {data.alerts.length > 0 && (
        <div className="card panel" style={{ marginTop: '1rem' }}>
          <div className="panel-head"><h3>هشدارها و پرونده‌ها</h3><span className="muted">{fmtNumber(data.alerts.length)} مورد اخیر</span></div>
          <div className="table-wrap">
            <table>
              <thead><tr><th>شناسه</th><th>عنوان</th><th>شدت</th><th>وضعیت</th><th className="num">امتیاز</th><th>زمان</th></tr></thead>
              <tbody>
                {data.alerts.map((alert) => (
                  <tr key={alert.alert_id} className="clickable" onClick={() => onOpenAlert?.(alert.alert_id)} tabIndex={0} onKeyDown={(event) => event.key === 'Enter' && onOpenAlert?.(alert.alert_id)}>
                    <td className="mono">{alert.alert_id}</td>
                    <td>{alert.title}</td>
                    <td><Badge kind="sev" value={alert.severity} labels={SEVERITY_LABELS} /></td>
                    <td><Badge kind="st" value={alert.status} labels={STATUS_LABELS} /></td>
                    <td className="num">{fmtScore(alert.risk_score)}</td>
                    <td>{fmtDate(alert.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <div className="card panel" style={{ marginTop: '1rem' }}>
        <div className="panel-head"><h3>تراکنش‌های اخیر</h3></div>
        {data.transactions.length === 0 ? <p className="muted">تراکنشی ثبت نشده است.</p> : (
          <div className="table-wrap">
            <table>
              <thead><tr><th>تراکنش</th><th>نوع</th><th className="num">مبلغ</th><th>وضعیت</th><th>تاریخ</th></tr></thead>
              <tbody>
                {data.transactions.map((txn) => (
                  <tr key={txn.transaction_id}>
                    <td className="mono">{txn.transaction_id}</td>
                    <td>{txn.transaction_type}</td>
                    <td className="num">{fmtAmount(txn.amount, txn.currency)}</td>
                    <td>{txn.is_suspicious ? <span className="badge sev-HIGH">مشکوک</span> : <span className="chip">{txn.status}</span>}</td>
                    <td>{fmtDate(txn.transaction_date)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <p className="muted">منبع داده: رکورد فعلی سامانه و تراکنش‌های نگهداری‌شده. زمان‌ها به وقت تهران و مبالغ به ریال نمایش داده می‌شوند.</p>
    </section>
  );
}

function CustomerSections({ data, roles }) {
  const { customer, riskScores } = data;
  return (
    <>
      <div className="grid-2" style={{ marginTop: '1rem' }}>
        <div className="card panel">
          <h3>اطلاعات شناسایی</h3>
          <div className="meta-grid">
            <div><span>نام</span><strong>{customer.first_name} {customer.last_name}</strong></div>
            <div><span>نوع</span><strong>{customer.customer_type === 'INDIVIDUAL' ? 'شخص حقیقی' : customer.customer_type === 'BUSINESS' ? 'کسب‌وکار' : customer.customer_type}</strong></div>
            <div><span>شناسهٔ ملی</span><strong className="mono" dir="ltr">{maskNationalId(customer.national_id, roles)}</strong></div>
            <div><span>ایمیل</span><strong dir="ltr">{maskEmail(customer.email, roles)}</strong></div>
            <div><span>شهر / استان</span><strong>{[customer.city, customer.province].filter(Boolean).join(' · ') || '—'}</strong></div>
            <div><span>کشور</span><strong dir="ltr">{customer.country || '—'}</strong></div>
            <div><span>وضعیت</span><strong>{customer.is_active ? 'فعال' : 'غیرفعال'}</strong></div>
            <div><span>تاریخ ثبت</span><strong>{fmtDate(customer.registration_date)}</strong></div>
          </div>
          {!roles.includes('COMPLIANCE_OFFICER') && <p className="muted">شناسهٔ ملی و ایمیل برای نقش‌های غیرانطباقی پوشانده شده‌اند.</p>}
        </div>
        <div className="card panel">
          <h3>روند امتیاز ریسک</h3>
          {riskScores.length < 2 ? <p className="muted">برای رسم روند به حداقل دو محاسبهٔ امتیاز نیاز است.</p> : <RiskTrend items={riskScores} />}
          <ul className="timeline" style={{ marginTop: '.8rem' }}>
            {riskScores.slice(0, 4).map((score) => (
              <li key={score.id}>
                <div className="tl-head"><span className="tl-type">{score.score_type === 'CUSTOMER' ? 'امتیاز مشتری' : 'امتیاز تراکنش'}</span><time>{fmtDate(score.calculated_at)}</time></div>
                <p>امتیاز {fmtScore(score.score)} · روش {score.calculation_method}</p>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </>
  );
}

function RiskTrend({ items }) {
  const points = [...items].reverse().slice(-20);
  const width = 320;
  const height = 70;
  const scores = points.map((item) => Number(item.score) || 0);
  const path = scores.map((score, index) => `${index === 0 ? 'M' : 'L'}${(index / Math.max(1, scores.length - 1)) * width},${height - (score / 100) * height}`).join(' ');
  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="sparkline" role="img" aria-label={`روند ${scores.length} محاسبهٔ اخیر امتیاز ریسک از ${fmtScore(scores[0])} به ${fmtScore(scores[scores.length - 1])}`}>
      <path d={path} fill="none" stroke="var(--primary)" strokeWidth="2.5" strokeLinejoin="round" />
    </svg>
  );
}

async function loadCustomer(customerId) {
  const [customer, riskScores, alerts, transactions] = await Promise.all([
    api.customer(customerId),
    api.customerRiskScores(customerId),
    api.customerAlerts(customerId),
    api.customerTransactions(customerId),
  ]);
  return {
    customer,
    riskScores,
    alerts: (Array.isArray(alerts) ? alerts : alerts.results || []).slice(0, 10),
    transactions: transactions.slice(0, 10),
    header: {
      id: customer.customer_id,
      title: `${customer.first_name} ${customer.last_name}`,
      kpis: [
        { label: 'سطح ریسک', value: SEVERITY_LABELS[customer.current_risk_level] || customer.current_risk_level },
        { label: 'امتیاز ریسک', value: fmtScore(customer.risk_score) },
        { label: 'هشدارها', value: fmtNumber(alerts.count ?? alerts.length) },
        { label: 'تراکنش‌ها', value: fmtNumber(transactions.length), hint: 'تا ۲۰۰ مورد اخیر' },
      ],
    },
  };
}

async function loadDevice(deviceId) {
  const device = await api.device(deviceId);
  const transactions = await api.transactions({ search: deviceId });
  const alerts = await api.alerts({ search: deviceId });
  const seen = transactions.results.filter((txn) => txn.device_detail?.device_id === deviceId);
  return {
    device,
    alerts: alerts.results.slice(0, 10),
    transactions: seen.slice(0, 10),
    notice: device.is_emulator || device.is_rooted ? 'این دستگاه نشانه‌های شبیه‌ساز یا دستکاری‌شدن دارد؛ بررسی انسانی لازم است.' : '',
    header: {
      id: device.device_id,
      title: [device.device_type, device.os, device.browser].filter(Boolean).join(' · ') || 'دستگاه بدون جزئیات فنی',
      kpis: [
        { label: 'آخرین مشاهده', value: fmtDate(device.last_seen_at) },
        { label: 'اولین مشاهده', value: fmtDate(device.first_seen_at) },
        { label: 'شبیه‌ساز', value: device.is_emulator ? 'بله' : 'خیر' },
        { label: 'روت/جیل‌بریک', value: device.is_rooted ? 'بله' : 'خیر' },
      ],
    },
  };
}

async function loadMerchant(merchantId) {
  const merchant = await api.merchant(merchantId);
  const alerts = await api.alerts({ search: merchantId });
  const transactions = await api.transactions({ search: merchantId });
  const seen = transactions.results.filter((txn) => txn.merchant_detail?.merchant_id === merchantId);
  return {
    merchant,
    alerts: alerts.results.slice(0, 10),
    transactions: seen.slice(0, 10),
    notice: 'نرخ بازگشت وجه و شارژبک فقط وقتی معنی‌دار است که حجم تراکنش کافی باشد.',
    header: {
      id: merchant.merchant_id,
      title: merchant.name || 'پذیرنده بدون نام',
      kpis: [
        { label: 'امتیاز ریسک', value: fmtScore(merchant.risk_score) },
        { label: 'نرخ شارژبک', value: `${fmtScore(merchant.chargeback_rate)}٪` },
        { label: 'نرخ بازگشت وجه', value: `${fmtScore(merchant.refund_rate)}٪` },
        { label: 'وضعیت', value: merchant.is_active ? 'فعال' : 'غیرفعال' },
      ],
    },
  };
}
