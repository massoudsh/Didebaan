import { useEffect, useRef, useState } from 'react';
import { api } from '../api.js';
import { fmtScore } from '../format.js';

const TYPES = [
  { id: 'alerts', label: 'هشدار / پرونده', placeholder: 'شناسه، عنوان یا توضیح هشدار' },
  { id: 'customers', label: 'مشتری / نهاد', placeholder: 'شناسه، نام، ایمیل یا شناسهٔ ملی' },
  { id: 'devices', label: 'دستگاه', placeholder: 'شناسهٔ دستگاه یا IP' },
  { id: 'merchants', label: 'پذیرنده', placeholder: 'شناسه یا نام پذیرنده' },
];

const LOADERS = {
  alerts: (q) => api.alerts({ search: q, ordering: '-created_at' }),
  customers: (q) => api.customers({ search: q }),
  devices: (q) => api.searchDevices(q),
  merchants: (q) => api.searchMerchants(q),
};

export default function SearchBar({ onNavigate }) {
  const [type, setType] = useState('alerts');
  const [query, setQuery] = useState('');
  const [state, setState] = useState({ open: false, loading: false, results: [], error: '' });
  const wrapper = useRef(null);

  useEffect(() => {
    const onDoc = (event) => {
      if (wrapper.current && !wrapper.current.contains(event.target)) setState((current) => ({ ...current, open: false }));
    };
    document.addEventListener('mousedown', onDoc);
    return () => document.removeEventListener('mousedown', onDoc);
  }, []);

  useEffect(() => {
    const q = query.trim();
    if (q.length < 2) {
      setState({ open: false, loading: false, results: [], error: '' });
      return undefined;
    }
    let active = true;
    setState((current) => ({ ...current, open: true, loading: true, error: '' }));
    const timer = setTimeout(() => {
      LOADERS[type](q)
        .then((data) => {
          if (!active) return;
          setState({ open: true, loading: false, error: '', results: (data.results || []).slice(0, 6) });
        })
        .catch((error) => active && setState({ open: true, loading: false, results: [], error: error.message }));
    }, 350);
    return () => { active = false; clearTimeout(timer); };
  }, [query, type]);

  function choose(item) {
    setState((current) => ({ ...current, open: false }));
    setQuery('');
    onNavigate(type, item);
  }

  const current = TYPES.find((item) => item.id === type);
  return (
    <div className="global-search" ref={wrapper}>
      <label className="sr-only" htmlFor="global-search-input">جست‌وجوی سراسری</label>
      <input
        id="global-search-input"
        type="search"
        value={query}
        onChange={(event) => setQuery(event.target.value)}
        onFocus={() => query.trim().length >= 2 && setState((s) => ({ ...s, open: true }))}
        onKeyDown={(event) => event.key === 'Escape' && setState((s) => ({ ...s, open: false }))}
        placeholder={`جست‌وجو در ${current.label}…`}
        aria-expanded={state.open}
        aria-controls="global-search-results"
        autoComplete="off"
      />
      <select value={type} onChange={(event) => setType(event.target.value)} aria-label="نوع جست‌وجو">
        {TYPES.map((item) => <option key={item.id} value={item.id}>{item.label}</option>)}
      </select>
      {state.open && (
        <div className="search-popover" id="global-search-results" role="listbox" aria-label="نتایج جست‌وجو">
          {state.loading && <p className="muted pad" role="status">در حال جست‌وجو…</p>}
          {state.error && <p className="error pad" role="alert">{state.error}</p>}
          {!state.loading && !state.error && state.results.length === 0 && <p className="muted pad">نتیجه‌ای پیدا نشد.</p>}
          {state.results.map((item) => (
            <button key={item.alert_id || item.customer_id || item.device_id || item.merchant_id} type="button" role="option" aria-selected="false" className="search-result" onClick={() => choose(item)}>
              <span className="mono">{item.alert_id || item.customer_id || item.device_id || item.merchant_id}</span>
              <small>{type === 'alerts' ? item.title : type === 'customers' ? `${item.first_name} ${item.last_name}` : item.name || '—'}</small>
              {item.risk_score !== undefined && item.risk_score !== null && <span className="chip">{fmtScore(item.risk_score)}</span>}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
