import { useEffect, useState } from 'react';
import { api } from '../api.js';
import { fmtNumber, fmtScore, SEVERITY_LABELS, STATUS_LABELS } from '../format.js';
import { DataTable, EmptyState, ErrorState, TableSkeleton } from './ui.jsx';

const LEVELS = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'];

function Bars({ data, labels, colorPrefix }) {
  const max = Math.max(1, ...Object.values(data));
  return (
    <ul className="bars">
      {Object.entries(data).map(([key, value]) => (
        <li key={key}>
          <span className="bar-label">{labels[key] || key}</span>
          <span className="bar-track">
            <span className={`bar-fill ${colorPrefix}-${key}`} style={{ width: `${(value / max) * 100}%` }} />
          </span>
          <span className="bar-value">{fmtNumber(value)}</span>
        </li>
      ))}
    </ul>
  );
}

export function outcomeRate(stats) {
  const { RESOLVED: resolved = 0, FALSE_POSITIVE: falsePositive = 0 } = stats?.by_status || {};
  const reviewed = resolved + falsePositive;
  return reviewed ? { rate: Math.round((falsePositive / reviewed) * 100), reviewed } : null;
}

export default function Dashboard({ onOpenQueue, onOpenEntity }) {
  const [days, setDays] = useState(30);
  const [state, setState] = useState({ loading: true });
  const [oldest, setOldest] = useState(null);

  useEffect(() => {
    let active = true;
    setState({ loading: true });
    Promise.all([api.statistics(days), api.openCount(), ...LEVELS.map((level) => api.alerts({ severity: level, status: 'OPEN', ordering: 'created_at', page: 1 }))])
      .then(([stats, open, ...queues]) => {
        if (!active) return;
        setState({ stats, open });
        const rows = queues.flatMap((page, index) => page.results.slice(0, 2).map((alert) => ({ ...alert, bucket: LEVELS[index] })));
        setOldest(rows);
      })
      .catch((error) => active && setState({ error: error.message }));
    return () => {
      active = false;
    };
  }, [days]);

  if (state.loading) return <><p className="muted pad" role="status">در حال بارگذاری مرکز فرماندهی…</p><TableSkeleton rows={3} columns={4} /></>;
  if (state.error) return <ErrorState message={state.error} />;

  const { stats, open } = state;
  const unresolved = stats.by_status.OPEN + stats.by_status.UNDER_REVIEW + stats.by_status.ESCALATED;
  const inProgress = stats.by_status.UNDER_REVIEW + stats.by_status.ESCALATED;
  const outcome = outcomeRate(stats);

  return (
    <section>
      <div className="hero-banner">
        <div>
          <span className="eyebrow accent">اتاق عملیات · پایش لحظه‌ای</span>
          <h2>از تراکنش مشکوک تا تصمیم قابل دفاع</h2>
          <p>یک نمای واحد برای کشف تقلب، انطباق ایرانی و رسیدگی سریع به پرونده‌ها.</p>
        </div>
        <button className="btn primary" onClick={() => onOpenQueue()}>باز کردن صف عملیات</button>
      </div>
      <div className="page-head">
        <div>
          <h2>تصویر ریسک</h2>
          <p className="muted">داده‌های زندهٔ {days === 7 ? '۷' : days === 30 ? '۳۰' : '۹۰'} روز اخیر · وضعیت پرونده‌ها در لحظه</p>
        </div>
        <div className="field">
          <label htmlFor="dashboard-range">بازه</label>
          <select id="dashboard-range" value={days} onChange={(e) => setDays(Number(e.target.value))}>
            <option value={7}>۷ روز اخیر</option>
            <option value={30}>۳۰ روز اخیر</option>
            <option value={90}>۹۰ روز اخیر</option>
          </select>
        </div>
      </div>

      <div className="kpi-grid" role="group" aria-label="شاخص‌های کلیدی">
        <button className="kpi" onClick={() => onOpenQueue()}>
          <span>هشدارهای باز</span><strong>{fmtNumber(open.TOTAL)}</strong><small>در انتظار رسیدگی · کلیک برای صف</small>
        </button>
        <button className="kpi alert" onClick={() => onOpenQueue({ severity: 'CRITICAL', status: 'OPEN' })}>
          <span>هشدارهای بحرانی باز</span><strong>{fmtNumber(open.CRITICAL)}</strong><small>اولویت بالاترین رسیدگی</small>
        </button>
        <button className="kpi warn" onClick={() => onOpenQueue({ status: 'OPEN' })}>
          <span>در انتظار تصمیم</span><strong>{fmtNumber(unresolved)}</strong><small>باز، در بررسی یا ارتقایافته</small>
        </button>
        <button className="kpi" onClick={() => onOpenQueue({ status: 'UNDER_REVIEW' })}>
          <span>پرونده‌های در جریان</span><strong>{fmtNumber(inProgress)}</strong><small>در بررسی و ارتقایافته</small>
        </button>
        <button className="kpi" onClick={() => onOpenQueue({ status: 'RESOLVED' })}>
          <span>حل‌شده (بازه)</span><strong>{fmtNumber(stats.by_status.RESOLVED)}</strong><small>تصمیم نهایی ثبت‌شده</small>
        </button>
        <button className="kpi ok" onClick={() => onOpenQueue({ status: 'FALSE_POSITIVE' })}>
          <span>نرخ مثبت کاذب</span><strong>{outcome ? `${fmtNumber(outcome.rate)}٪` : '—'}</strong><small>{outcome ? `از ${fmtNumber(outcome.reviewed)} پروندهٔ رسیدگی‌شده` : 'با اولین تصمیم نهایی نمایش داده می‌شود'}</small>
        </button>
      </div>

      <div className="grid-2">
        <div className="card panel">
          <div className="panel-head"><h3>شدت هشدارها</h3><span className="muted">میانگین امتیاز {fmtScore(stats.average_risk_score)}</span></div>
          <Bars data={stats.by_severity} labels={SEVERITY_LABELS} colorPrefix="sev" />
        </div>
        <div className="card panel">
          <div className="panel-head"><h3>وضعیت رسیدگی</h3></div>
          <Bars data={stats.by_status} labels={STATUS_LABELS} colorPrefix="st" />
        </div>
        <div className="card panel">
          <div className="panel-head"><h3>قدیمی‌ترین پرونده‌های باز</h3><button className="btn ghost" onClick={() => onOpenQueue({ ordering: 'created_at' })}>نمایش همه</button></div>
          {oldest === null ? <p className="muted">در حال بارگذاری…</p> : <DataTable
            columns={[
              { key: 'alert_id', header: 'شناسه', render: (alert) => <span className="mono">{alert.alert_id}</span> },
              { key: 'bucket', header: 'شدت', render: (alert) => SEVERITY_LABELS[alert.bucket] },
              { key: 'customer', header: 'مشتری', render: (alert) => alert.customer_detail?.customer_id || '—' },
            ]}
            rows={oldest}
            rowKey={(alert) => alert.alert_id}
            empty="هشدار باز توسط این بخش دریافت نشد."
            onRowClick={(alert) => onOpenQueue({ severity: alert.bucket, status: 'OPEN' })}
          />}
        </div>
        <div className="card compliance-card panel">
          <div className="card-kicker">انطباق برای بازار ایران</div>
          <h3>ردپای تصمیم آمادهٔ ممیزی</h3>
          <p className="muted">هر هشدار با علت، قانون فعال، بررسی‌کننده و تاریخچهٔ تغییرات نگهداری می‌شود.</p>
          <div className="compliance-tags"><span>ریال IRR</span><span>CTR</span><span>PEP</span><span>FATF</span></div>
          <div className="row-gap">
            <button className="btn" onClick={() => onOpenQueue()}>مشاهدهٔ پرونده‌ها</button>
            <button className="btn ghost" onClick={() => onOpenEntity({ kind: 'customer', id: 'DEMO-C1', label: 'DEMO-C1' })}>نمونهٔ پروفایل مشتری</button>
          </div>
          <p className="muted" style={{ marginTop: '.8rem' }}>داده‌های نمونه و فهرست‌های کشور، معیار حقوقی تأییدشده نیستند؛ نرخ‌ها به بازبینی انسانی وابسته‌اند.</p>
        </div>
      </div>

      {!stats.total && <EmptyState title="در این بازه هشداری ثبت نشده">دادهٔ نمونه را با seed_demo بسازید یا بازه را گسترش دهید.</EmptyState>}
    </section>
  );
}
