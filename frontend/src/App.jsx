import { useCallback, useEffect, useRef, useState } from 'react';
import { api, auth, healthStatus } from './api.js';
import Login from './components/Login.jsx';
import Dashboard from './components/Dashboard.jsx';
import AlertQueue from './components/AlertQueue.jsx';
import Intelligence from './components/Intelligence.jsx';
import EntityProfile from './components/entities/EntityProfile.jsx';
import RuleCatalog from './components/rules/RuleCatalog.jsx';
import CaseInbox from './components/cases/CaseInbox.jsx';
import SearchBar from './components/SearchBar.jsx';
import { IconButton } from './components/ui.jsx';

const TABS = [
  { id: 'dashboard', label: 'مرکز فرماندهی', icon: '⌂' },
  { id: 'alerts', label: 'صف عملیات', icon: '◈' },
  { id: 'cases', label: 'کارتابل پرونده‌ها', icon: '▤' },
  { id: 'intelligence', label: 'تحلیل و انطباق', icon: '◇' },
  { id: 'rules', label: 'قوانین و شفافیت', icon: '☰', hint: 'خواندنی برای همهٔ نقش‌ها' },
];

const ENTITY_TAB = { id: 'entity', label: 'پروفایل موجودیت', icon: '◎' };

const ROLE_LABELS = {
  AUDITOR: 'ممیز',
  INVESTIGATOR: 'بررسی‌کننده',
  SUPERVISOR: 'سرپرست',
  COMPLIANCE_OFFICER: 'افسر انطباق',
};

const ENVIRONMENT = import.meta.env?.VITE_ENVIRONMENT || (import.meta.env?.DEV ? 'development' : 'production');
const ENV_LABELS = { development: 'محیط توسعه', staging: 'محیط آزمایشی', sandbox: 'سندباکس', production: 'تولید' };

function readTheme() {
  const saved = localStorage.getItem('didebaan.theme');
  if (saved) return saved;
  return globalThis.matchMedia?.('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

export default function App() {
  const [user, setUser] = useState(
    auth.token ? { username: auth.user, roles: auth.roles } : null,
  );
  const [view, setView] = useState({ tab: 'alerts' });
  const [theme, setTheme] = useState(readTheme);
  const [menuOpen, setMenuOpen] = useState(false);
  const [status, setStatus] = useState('checking');
  const [critical, setCritical] = useState(null);
  const contentRef = useRef(null);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem('didebaan.theme', theme);
  }, [theme]);

  useEffect(() => {
    let active = true;
    const check = () => healthStatus().then((value) => active && setStatus(value));
    check();
    const timer = setInterval(check, 60000);
    const onOffline = () => setStatus('offline');
    const onOnline = () => check();
    globalThis.addEventListener?.('offline', onOffline);
    globalThis.addEventListener?.('online', onOnline);
    return () => {
      active = false;
      clearInterval(timer);
      globalThis.removeEventListener?.('offline', onOffline);
      globalThis.removeEventListener?.('online', onOnline);
    };
  }, []);

  const logout = useCallback(() => {
    auth.clear();
    setUser(null);
  }, []);

  useEffect(() => {
    auth.onUnauthorized(() => setUser(null));
  }, []);

  useEffect(() => {
    if (!user) return undefined;
    let active = true;
    api.openCount()
      .then((data) => active && setCritical(data.CRITICAL || 0))
      .catch(() => active && setCritical(null));
    return () => { active = false; };
  }, [user, view]);

  useEffect(() => {
    setMenuOpen(false);
    contentRef.current?.focus({ preventScroll: true });
  }, [view]);

  if (!user) return <Login onLogin={setUser} />;

  const tab = view.tab === 'entity' ? 'cases' : view.tab;
  const navItems = view.tab === 'entity' ? [...TABS, ENTITY_TAB] : TABS;

  function navigate(type, item) {
    if (type === 'alerts') setView({ tab: 'cases', alertId: item.alert_id });
    else if (type === 'customers') setView({ tab: 'entity', entity: { kind: 'customer', id: item.customer_id, label: item.customer_id } });
    else setView({ tab: 'entity', entity: { kind: type === 'devices' ? 'device' : 'merchant', id: item.device_id || item.merchant_id, label: item.name || item.device_id || item.merchant_id } });
  }

  const envLabel = ENV_LABELS[ENVIRONMENT] || ENVIRONMENT;

  return (
    <div className="shell">
      <a className="skip-link" href="#main-content">پرش به محتوای اصلی</a>
      <header className="topbar">
        <IconButton label={menuOpen ? 'بستن منوی ناوبری' : 'باز کردن منوی ناوبری'} className="menu-toggle" aria-expanded={menuOpen} aria-controls="main-sidebar" onClick={() => setMenuOpen((open) => !open)}>☰</IconButton>
        <div className="brand">
          <span className="brand-mark" aria-hidden="true">د</span>
          <div>
            <h1>دیده‌بان</h1>
            <p>اتاق عملیات ریسک ایران</p>
          </div>
        </div>
        <SearchBar onNavigate={navigate} />
        <div className="topbar-actions">
          <span className={`env-chip ${ENVIRONMENT === 'production' ? 'production' : ''}`} title="محیط اجرای برنامه">{envLabel}</span>
          <span className={`system-state ${status === 'offline' ? 'offline' : ''}`} role="status">
            <span className={`pulse-dot ${status === 'offline' ? 'offline' : ''}`} />
            {status === 'offline' ? 'قطع ارتباط' : status === 'online' ? 'سرویس متصل' : 'بررسی سرویس…'}
          </span>
          <button className="btn ghost" onClick={() => setView({ tab: 'alerts', filter: { severity: 'CRITICAL', status: 'OPEN' } })} aria-label={critical ? `${critical} هشدار بحرانی باز` : 'هشدارهای بحرانی'}>
            <span aria-hidden="true">⚠</span> {critical === null ? 'بحرانی' : `${critical} بحرانی`}
          </button>
          <button className="btn ghost" onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')} aria-label={theme === 'light' ? 'فعال‌سازی حالت تیره' : 'فعال‌سازی حالت روشن'}>
            {theme === 'light' ? '☾' : '☀'}
          </button>
          <div className="user-menu">
            <span className="user-chip" dir="ltr">{user.username}</span>
            <small>{user.roles.map((role) => ROLE_LABELS[role] || role).join('، ') || 'مدیر سیستم'}</small>
          </div>
          <button className="btn ghost" onClick={logout}>خروج</button>
        </div>
      </header>
      <div className="workspace">
        <aside id="main-sidebar" className={`sidebar${menuOpen ? ' open' : ''}`} aria-label="ناوبری اصلی">
          <p className="eyebrow">مرکز کنترل</p>
          <nav className="side-nav">
            {navItems.map((item) => (
              <button
                key={item.id}
                className={view.tab === item.id ? 'side-link active' : 'side-link'}
                aria-current={view.tab === item.id ? 'page' : undefined}
                onClick={() => setView({ tab: item.id })}
              >
                <span className="side-icon" aria-hidden="true">{item.icon}</span>{item.label}
              </button>
            ))}
          </nav>
          <div className="sidebar-footer">
            <span className="eyebrow">بازار هدف</span>
            <strong>ایران · ریال</strong>
            <small>قوانین CTR، PEP و تحریم</small>
          </div>
        </aside>
        <main className="content" id="main-content" ref={contentRef} tabIndex={-1}>
          {tab === 'dashboard' && <Dashboard onOpenQueue={(filter) => setView({ tab: 'alerts', filter })} onOpenEntity={(entity) => setView({ tab: 'entity', entity })} />}
          {tab === 'alerts' && <AlertQueue key={JSON.stringify(view)} initial={view} currentUser={user.username} roles={user.roles} onOpenEntity={(entity) => setView({ tab: 'entity', entity })} />}
          {tab === 'cases' && <CaseInbox key={JSON.stringify(view)} initial={view} currentUser={user.username} roles={user.roles} />}
          {tab === 'intelligence' && <Intelligence roles={user.roles} onOpenEntity={(entity) => setView({ tab: 'entity', entity })} />}
          {tab === 'rules' && <RuleCatalog roles={user.roles} />}
          {view.tab === 'entity' && <EntityProfile entity={view.entity} roles={user.roles} onBack={() => setView({ tab: 'cases' })} onOpenAlert={(alertId) => setView({ tab: 'cases', alertId })} />}
        </main>
      </div>
    </div>
  );
}
