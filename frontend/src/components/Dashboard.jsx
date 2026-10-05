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
      <div className="page-head">
        <div>
          <h2>داشبورد ریسک</h2>
          <p className="muted">خلاصهٔ هشدارها و مشتریان بر اساس داده‌های زنده</p>
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
