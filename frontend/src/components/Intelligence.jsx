import { useEffect, useState } from 'react';
import { api } from '../api.js';
import { fmtDate, fmtNumber, fmtScore } from '../format.js';

const TOOLS = [
  ['simulate', 'آزمایش قوانین', 'مقایسهٔ تنظیمات فعلی و پیشنهادی بدون تغییر داده‌های عملیاتی'],
  ['graph', 'شبکهٔ ارتباطات', 'ردیابی دستگاه، پذیرنده و حساب مقصد مشتری'],
  ['screen', 'غربالگری فارسی', 'تطبیق نام فارسی و شناسهٔ ملی با فهرست پایش'],
  ['sla', 'مهلت رسیدگی', 'نمایش پرونده‌های دیرکرددار و نزدیک به پایان مهلت'],
  ['export', 'بستهٔ شواهد', 'دریافت هشدار، دلایل، تاریخچه و تصویر فعلی قوانین'],
];
const SIMULATION_TYPES = ['THRESHOLD', 'PATTERN', 'BEHAVIORAL', 'GEOGRAPHIC'];

function RelationshipGraph({ data }) {
  const visible = data.nodes.slice(0, 25);
  const center = { x: 360, y: 220 };
  const positions = visible.map((node, index) => {
    const angle = (index - 1) * 2 * Math.PI / Math.max(1, visible.length - 1);
    return index === 0 ? center : { x: 360 + 260 * Math.cos(angle), y: 220 + 160 * Math.sin(angle) };
  });
  return (
    <>
      <svg className="relationship-graph" viewBox="0 0 720 440" role="img" aria-label="شبکهٔ ارتباط مشتری؛ جزئیات در جدول زیر">
        {visible.slice(1).map((node, index) => <line key={node.id} x1={center.x} y1={center.y} x2={positions[index + 1].x} y2={positions[index + 1].y} stroke="var(--border)" strokeWidth="2" />)}
        {visible.map((node, index) => <g key={node.id} transform={`translate(${positions[index].x},${positions[index].y})`}>
          <circle r={index === 0 ? 30 : 14} fill={index === 0 ? 'var(--primary)' : 'var(--primary-soft)'} stroke="var(--primary)" />
          <text y={index === 0 ? 50 : 30} textAnchor="middle" fill="var(--text)" fontSize="12">{node.label.length > 20 ? `${node.label.slice(0, 17)}…` : node.label}</text>
          <title>{node.kind}: {node.label}</title>
        </g>)}
      </svg>
      {data.nodes.length > 25 && <p className="muted">نمودار فقط ۲۵ گرهٔ اول را نشان می‌دهد؛ همهٔ ارتباطات نمونه در جدول آمده‌اند.</p>}
      <div className="table-wrap"><table className="intelligence-table"><thead><tr><th>نوع ارتباط</th><th>شناسه</th><th>تراکنش در نمونه</th></tr></thead><tbody>
        {data.edges.map((edge) => {
          const node = data.nodes.find((item) => item.id === edge.target);
          return <tr key={edge.target}><td>{({ device: 'دستگاه', merchant: 'پذیرنده', account: 'حساب مقصد' })[node.kind]}</td><td dir="ltr">{node.label}</td><td>{fmtNumber(edge.transactions)}</td></tr>;
        })}
      </tbody></table></div>
    </>
  );
}

export default function Intelligence({ roles = [] }) {
  const compliance = roles.includes('COMPLIANCE_OFFICER');
  const [tool, setTool] = useState('graph');
  const [rules, setRules] = useState([]);
  const [rulesPage, setRulesPage] = useState(1);
  const [moreRules, setMoreRules] = useState(false);
  const [ruleError, setRuleError] = useState('');
  const [ruleLoading, setRuleLoading] = useState(false);
  const [ruleId, setRuleId] = useState('');
  const [configuration, setConfiguration] = useState('{\n  "amount_threshold": 100000000\n}');
  const [customerId, setCustomerId] = useState('');
  const [name, setName] = useState('');
  const [nationalId, setNationalId] = useState('');
  const [score, setScore] = useState(85);
  const [alertId, setAlertId] = useState('');
  const [days, setDays] = useState(30);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);

  useEffect(() => {
    if (!compliance) return undefined;
    let active = true;
    setRuleLoading(true);
    api.rules({ page: rulesPage }).then((data) => {
      if (!active) return;
      setRules((current) => rulesPage === 1 ? data.results : [...current, ...data.results]);
      setMoreRules(Boolean(data.next));
      setRuleError('');
    }).catch((err) => active && setRuleError(err.message)).finally(() => active && setRuleLoading(false));
    return () => { active = false; };
  }, [compliance, rulesPage]);

  function selectTool(next) {
    setTool(next);
    setResult(null);
    setError('');
  }

  async function submit(event) {
    event.preventDefault();
    setBusy(true);
    setError('');
    setResult(null);
    try {
      let data;
      if (tool === 'simulate') {
        let parsed;
        try { parsed = JSON.parse(configuration); } catch { throw new Error('تنظیمات قانون باید JSON معتبر باشد.'); }
        data = await api.simulate({ rule_id: ruleId, configuration: parsed, days, limit: 100 });
      } else if (tool === 'graph') data = await api.graph({ customer_id: customerId.trim(), days });
      else if (tool === 'screen') data = await api.screen({ name, national_id: nationalId, minimum_score: score });
      else if (tool === 'sla') data = await api.sla();
      else { await api.exportCase(alertId.trim()); data = { downloaded: true }; }
      setResult(data);
    } catch (err) { setError(err.message); }
    finally { setBusy(false); }
  }

  return <section>
    <div className="page-head"><div><h2>ابزارهای تحلیل و انطباق</h2><p className="muted">تحلیل مبتنی بر شواهد؛ هیچ‌یک از این ابزارها تراکنش را مسدود یا قانون را فعال نمی‌کند.</p></div></div>
    <div className="analysis-tools" role="group" aria-label="انتخاب ابزار">
      {TOOLS.filter(([id]) => compliance || !['simulate', 'screen'].includes(id)).map(([id, title]) => <button key={id} disabled={busy} className={`btn ${id === tool ? 'primary' : ''}`} aria-pressed={id === tool} onClick={() => selectTool(id)}>{title}</button>)}
    </div>
    <div className="card analysis-panel">
      <h3>{TOOLS.find(([id]) => id === tool)[1]}</h3><p className="muted">{TOOLS.find(([id]) => id === tool)[2]}</p>
      <form className="stack" onSubmit={submit} aria-busy={busy}>
        {tool === 'simulate' && <>
          <p className="notice">چهار نوع قانون پشتیبانی می‌شود: آستانه، الگو، رفتار و جغرافیا. بازه‌ها نسبت به زمان تراکنش محاسبه می‌شوند؛ مشخصات مشتری تصویر تاریخی نیست.</p>
          {ruleError && <p className="error" role="alert">{ruleError}</p>}
          <label>قانون<select required value={ruleId} onChange={(e) => { setRuleId(e.target.value); setConfiguration(JSON.stringify(rules.find((r) => r.id === e.target.value).configuration, null, 2)); }}>
            <option value="">انتخاب قانون</option>{rules.filter((r) => SIMULATION_TYPES.includes(r.rule_type)).map((r) => <option key={r.id} value={r.id}>{r.name} · {r.status}</option>)}
          </select></label>
          {ruleLoading && <p role="status">بارگذاری قوانین…</p>}
          {moreRules && <button type="button" className="btn" disabled={ruleLoading} onClick={() => setRulesPage((page) => page + 1)}>بارگذاری قوانین بیشتر</button>}
          {!ruleLoading && rules.length === 0 && <p className="muted">قانونی یافت نشد؛ ابتدا قانون را در مدیریت ایجاد کنید.</p>}
          <label>تنظیمات پیشنهادی (JSON)<textarea dir="ltr" rows={7} value={configuration} onChange={(e) => setConfiguration(e.target.value)} required /></label>
        </>}
        {tool === 'graph' && <label>شناسهٔ مشتری<input dir="ltr" required maxLength={100} value={customerId} onChange={(e) => setCustomerId(e.target.value)} /></label>}
        {['graph', 'simulate'].includes(tool) && <label>بازهٔ بررسی<select value={days} onChange={(e) => setDays(Number(e.target.value))}><option value={7}>۷ روز</option><option value={30}>۳۰ روز</option><option value={90}>۹۰ روز</option></select></label>}
        {tool === 'screen' && <>
          <div className="grid-2"><label>نام شخص یا نهاد<input maxLength={200} value={name} onChange={(e) => setName(e.target.value)} /></label><label>شناسهٔ ملی<input maxLength={50} value={nationalId} onChange={(e) => setNationalId(e.target.value)} /></label></div>
          <label>حداقل شباهت نام (۷۰ تا ۱۰۰)<input type="number" min={70} max={100} required value={score} onChange={(e) => setScore(Number(e.target.value))} /></label>
          <p className="muted">ک/ك، ی/ي، ارقام فارسی و اعراب یکسان‌سازی می‌شوند. نتیجهٔ مشابه، اثبات تخلف نیست.</p>
        </>}
        {tool === 'export' && <><label>شناسهٔ هشدار<input dir="ltr" required maxLength={100} value={alertId} onChange={(e) => setAlertId(e.target.value)} /></label><p className="muted">خروجی JSON شامل اطلاعات حساس پرونده است؛ فقط در مسیر مجاز سازمان به اشتراک بگذارید. قالب ارسال رسمی به رگولاتور نیست.</p></>}
        <button className="btn primary" disabled={busy || (tool === 'screen' && !name.trim() && !nationalId.trim())}>{busy ? 'در حال پردازش…' : tool === 'export' ? 'دریافت بستهٔ شواهد' : 'اجرای بررسی'}</button>
      </form>
    </div>
    {error && <p className="error" role="alert">{error}</p>}
    {result && <div className="card analysis-panel" aria-live="polite">
      <h3>نتیجهٔ بررسی</h3>
      {result.truncated && <p className="notice">نتایج محدود به نمونه هستند؛ این گزارش کل داده‌ها را پوشش نمی‌دهد.</p>}
      {tool === 'simulate' && <>
        <p>بررسی {fmtNumber(result.evaluated_count)} از {fmtNumber(result.eligible_count)} تراکنش · نسخهٔ قانون {fmtNumber(result.rule_version)}</p>
        <div className="stat-grid"><div className="stat"><span>تطبیق فعلی</span><strong>{fmtNumber(result.baseline_matches)}</strong></div><div className="stat"><span>تطبیق پیشنهادی</span><strong>{fmtNumber(result.candidate_matches)}</strong></div><div className="stat"><span>تطبیق جدید</span><strong>{fmtNumber(result.new_matches)}</strong></div><div className="stat"><span>تطبیق حذف‌شده</span><strong>{fmtNumber(result.removed_matches)}</strong></div></div>
        <div className="table-wrap"><table className="intelligence-table"><thead><tr><th>تراکنش</th><th>امتیاز فعلی</th><th>امتیاز پیشنهادی</th><th>تطبیق فعلی / پیشنهادی</th><th>دلیل پیشنهادی</th></tr></thead><tbody>{result.results.map((r) => <tr key={r.transaction_id}><td dir="ltr">{r.transaction_id}</td><td>{fmtScore(r.baseline_score)}</td><td>{fmtScore(r.candidate_score)}</td><td>{r.baseline_match ? 'بله' : 'خیر'} / {r.candidate_match ? 'بله' : 'خیر'}</td><td>{r.reason || '—'}</td></tr>)}</tbody></table></div>
        {result.evaluated_count === 0 && <p className="muted">تراکنش تکمیل‌شده‌ای در این بازه وجود ندارد.</p>}
      </>}
      {tool === 'graph' && <>
        <p>{fmtNumber(result.sampled_count)} از {fmtNumber(result.eligible_count)} تراکنش · ارتباط مشترک به‌تنهایی نشانهٔ تقلب نیست.</p>
        <RelationshipGraph data={result} />
        {!result.edges.length && <p className="muted">ارتباطی در این بازه پیدا نشد.</p>}
        <h3>مشتریان دارای دستگاه یا پذیرندهٔ مشترک</h3>
        {result.related_customers.map((peer) => <p key={peer.customer__customer_id}><b dir="ltr">{peer.customer__customer_id}</b> · {fmtNumber(peer.transactions)} تراکنش مرتبط</p>)}
        {result.related_truncated && <p className="notice">فقط ۵۰ مشتری مرتبط اول نمایش داده می‌شود.</p>}
        {!result.related_customers.length && <p className="muted">مشتری مرتبطی پیدا نشد.</p>}
      </>}
      {tool === 'screen' && <>
        <p>{fmtNumber(result.screened_count)} مورد بررسی و {fmtNumber(result.match_count)} تطبیق احتمالی؛ تصمیم نهایی نیازمند بررسی انسانی است.</p>
        {result.matches.map((match) => <div className="screening-match" key={match.id}><strong>{match.name || 'بدون نام'}</strong><span>{match.source_list || 'منبع ثبت نشده'} · {match.match_type === 'national_id' ? 'شناسهٔ ملی یکسان' : 'شباهت نام'} · {fmtNumber(match.score)}٪</span></div>)}
        {!result.matches.length && <p className="muted">تطبیقی با این آستانه یافت نشد؛ این نتیجه تأیید هویت یا تضمین نبود ریسک نیست.</p>}
      </>}
      {tool === 'sla' && <>
        <p>مهلت {fmtNumber(result.sla_hours)} ساعت · زمان گزارش {fmtDate(result.as_of)}</p>
        <div className="stat-grid"><div className="stat"><span>ارجاع‌شدهٔ باز</span><strong>{fmtNumber(result.assigned_open)}</strong></div><div className="stat warn"><span>دیرکرد</span><strong>{fmtNumber(result.overdue)}</strong></div><div className="stat"><span>نزدیک سررسید (۲۰٪ پایانی)</span><strong>{fmtNumber(result.due_soon)}</strong></div><div className="stat"><span>بدون ارجاع</span><strong>{fmtNumber(result.unassigned_open)}</strong></div></div>
        <div className="table-wrap"><table className="intelligence-table"><thead><tr><th>هشدار</th><th>بررسی‌کننده</th><th>سررسید</th><th>وضعیت مهلت</th></tr></thead><tbody>{result.results.map((r) => <tr key={r.alert_id}><td dir="ltr">{r.alert_id}</td><td>{r.assigned_to}</td><td>{fmtDate(r.due_at)}</td><td>{r.overdue ? 'دیرکرد' : 'در مهلت'}</td></tr>)}</tbody></table></div>
        {!result.results.length && <p className="muted">پروندهٔ باز ارجاع‌شده‌ای وجود ندارد.</p>}
      </>}
      {tool === 'export' && <p className="notice">بستهٔ شواهد برای دانلود ارسال شد.</p>}
    </div>}
  </section>;
}
