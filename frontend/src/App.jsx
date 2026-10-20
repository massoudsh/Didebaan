import { useCallback, useEffect, useState } from 'react';
import { auth } from './api.js';
import Login from './components/Login.jsx';
import Dashboard from './components/Dashboard.jsx';
import AlertQueue from './components/AlertQueue.jsx';

const TABS = [
  { id: 'dashboard', label: 'مرکز فرماندهی', icon: '⌂' },
  { id: 'alerts', label: 'صف عملیات', icon: '◈' },
];

const ROLE_LABELS = {
  AUDITOR: 'ممیز',
  INVESTIGATOR: 'بررسی‌کننده',
  SUPERVISOR: 'سرپرست',
  COMPLIANCE_OFFICER: 'افسر انطباق',
};

function readTheme() {
  return localStorage.getItem('didebaan.theme') || 'light';
}

export default function App() {
  const [user, setUser] = useState(
    auth.token ? { username: auth.user, roles: auth.roles } : null,
  );
  const [tab, setTab] = useState('alerts');
  const [theme, setTheme] = useState(readTheme);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem('didebaan.theme', theme);
  }, [theme]);

  const logout = useCallback(() => {
    auth.clear();
    setUser(null);
  }, []);

  useEffect(() => {
    auth.onUnauthorized(() => setUser(null));
  }, []);

  if (!user) return <Login onLogin={setUser} />;

  return (
    <div className="shell">
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark" aria-hidden="true">د</span>
          <div>
            <h1>دیده‌بان</h1>
            <p>اتاق عملیات ریسک ایران</p>
          </div>
        </div>
        <div className="system-state"><span className="pulse-dot" /> پایش فعال <small>آخرین همگام‌سازی: اکنون</small></div>
        <div className="topbar-actions">
          <button className="btn ghost" onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')}>
            {theme === 'light' ? 'حالت تیره' : 'حالت روشن'}
          </button>
          <div className="user-menu">
            <span className="user-chip" dir="ltr">{user.username}</span>
            <small>{user.roles.map((role) => ROLE_LABELS[role] || role).join('، ') || 'مدیر سیستم'}</small>
          </div>
          <button className="btn ghost" onClick={logout}>خروج</button>
        </div>
      </header>
      <div className="workspace">
        <aside className="sidebar" aria-label="ناوبری اصلی">
          <p className="eyebrow">مرکز کنترل</p>
          <nav className="side-nav">
            {TABS.map((item) => (
              <button
                key={item.id}
                className={tab === item.id ? 'side-link active' : 'side-link'}
                aria-current={tab === item.id ? 'page' : undefined}
                onClick={() => setTab(item.id)}
              >
                <span className="side-icon">{item.icon}</span>{item.label}
              </button>
            ))}
          </nav>
          <div className="sidebar-footer">
            <span className="eyebrow">بازار هدف</span>
            <strong>ایران · ریال</strong>
            <small>قوانین CTR، PEP و تحریم</small>
          </div>
        </aside>
        <main className="content">
          {tab === 'dashboard' ? <Dashboard onOpenQueue={() => setTab('alerts')} /> : <AlertQueue currentUser={user.username} roles={user.roles} />}
        </main>
      </div>
    </div>
  );
}
