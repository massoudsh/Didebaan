import { useEffect, useState } from 'react';
import { api } from '../api.js';
import { fmtNumber, fmtScore, SEVERITY_LABELS, STATUS_LABELS } from '../format.js';

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

export default function Dashboard({ onOpenQueue }) {
  const [days, setDays] = useState(30);
  const [state, setState] = useState({ loading: true });

  useEffect(() => {
    let active = true;
    setState({ loading: true });
    Promise.all([api.statistics(days), api.openCount(), ...LEVELS.map(api.customerCount)])
      .then(([stats, open, ...counts]) => {
        if (!active) return;
        const customers = Object.fromEntries(LEVELS.map((level, i) => [level, counts[i]]));
        setState({ stats, open, customers });
      })
      .catch((error) => active && setState({ error: error.message }));
    return () => {
      active = false;
    };
  }, [days]);

  if (state.loading) return <p className="muted pad">در حال بارگذاری…</p>;
  if (state.error) return <p className="error pad" role="alert">{state.error}</p>;

  const { stats, open, customers } = state;
  const unresolved = stats.by_status.OPEN + stats.by_status.UNDER_REVIEW + stats.by_status.ESCALATED;

  return (
    <section>
      <div className="hero-banner">
        <div>
          <span className="eyebrow accent">اتاق عملیات · پایش لحظه‌ای</span>
          <h2>از تراکنش مشکوک تا تصمیم قابل دفاع</h2>
          <p>یک نمای واحد برای کشف تقلب، انطباق ایرانی و رسیدگی سریع به پرونده‌ها.</p>
        </div>
        <button className="btn primary" onClick={onOpenQueue}>باز کردن صف عملیات</button>
      </div>
      <div className="page-head">
        <div>
          <h2>تصویر ریسک</h2>
          <p className="muted">داده‌های زندهٔ پایش تراکنش و وضعیت پرونده‌ها</p>
        </div>
        <label className="inline">
          بازه
          <select value={days} onChange={(e) => setDays(Number(e.target.value))}>
            <option value={7}>۷ روز اخیر</option>
            <option value={30}>۳۰ روز اخیر</option>
            <option value={90}>۹۰ روز اخیر</option>
          </select>
        </label>
      </div>

      <div className="feature-strip">
        <div><b>۰۱</b><span>پایش زنده</span><small>تصمیم پیش از تسویه</small></div>
        <div><b>۰۲</b><span>هوش رفتاری</span><small>الگوی مشتری و شبکه</small></div>
        <div><b>۰۳</b><span>انطباق ایرانی</span><small>CTR، PEP و watchlist</small></div>
        <div><b>۰۴</b><span>پروندهٔ قابل دفاع</span><small>دلیل، اقدام و تاریخچه</small></div>
        <div><b>۰۵</b><span>SLA عملیاتی</span><small>اولویت‌بندی بر اساس زمان</small></div>
      </div>

      <div className="stat-grid">
        <div className="stat"><span>کل هشدارها</span><strong>{fmtNumber(stats.total)}</strong></div>
        <div className="stat"><span>هشدار باز</span><strong>{fmtNumber(open.TOTAL)}</strong></div>
        <div className="stat warn"><span>در انتظار تصمیم</span><strong>{fmtNumber(unresolved)}</strong></div>
        <div className="stat"><span>میانگین امتیاز ریسک</span><strong>{fmtScore(stats.average_risk_score)}</strong></div>
      </div>

      <div className="grid-2">
        <div className="card">
          <h3>شدت هشدارها</h3>
          <Bars data={stats.by_severity} labels={SEVERITY_LABELS} colorPrefix="sev" />
        </div>
        <div className="card">
          <h3>وضعیت رسیدگی</h3>
          <Bars data={stats.by_status} labels={STATUS_LABELS} colorPrefix="st" />
        </div>
        <div className="card">
          <h3>سطح ریسک مشتریان</h3>
          <Bars data={customers} labels={SEVERITY_LABELS} colorPrefix="sev" />
        </div>
        <div className="card compliance-card">
          <div className="card-kicker">انطباق برای بازار ایران</div>
          <h3>ردپای تصمیم آمادهٔ ممیزی</h3>
          <p className="muted">هر هشدار با علت، قانون فعال، بررسی‌کننده و تاریخچهٔ تغییرات نگهداری می‌شود.</p>
          <div className="compliance-tags"><span>ریال IRR</span><span>CTR</span><span>PEP</span><span>FATF</span></div>
          <button className="btn" onClick={onOpenQueue}>مشاهدهٔ پرونده‌ها</button>
        </div>
        <div className="card">
          <h3>هشدارهای باز بر اساس شدت</h3>
          <Bars
            data={{ LOW: open.LOW, MEDIUM: open.MEDIUM, HIGH: open.HIGH, CRITICAL: open.CRITICAL }}
            labels={SEVERITY_LABELS}
            colorPrefix="sev"
          />
          <button className="btn primary" onClick={onOpenQueue}>رفتن به صف هشدارها</button>
        </div>
      </div>
    </section>
  );
}
