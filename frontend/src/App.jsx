import { useCallback, useEffect, useState } from 'react';
import { auth } from './api.js';
import Login from './components/Login.jsx';
import Dashboard from './components/Dashboard.jsx';
import AlertQueue from './components/AlertQueue.jsx';

const TABS = [
  { id: 'dashboard', label: 'داشبورد ریسک' },
  { id: 'alerts', label: 'صف هشدارها' },
];

function readTheme() {
  return localStorage.getItem('didebaan.theme') || 'light';
}

export default function App() {
  const [user, setUser] = useState(auth.token ? auth.user : null);
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
            <p>مرکز بررسی هشدارها</p>
          </div>
        </div>
        <nav className="tabs" aria-label="بخش‌ها">
          {TABS.map((item) => (
            <button
              key={item.id}
              className={tab === item.id ? 'tab active' : 'tab'}
              aria-current={tab === item.id ? 'page' : undefined}
              onClick={() => setTab(item.id)}
            >
              {item.label}
            </button>
          ))}
        </nav>
        <div className="topbar-actions">
          <button className="btn ghost" onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')}>
            {theme === 'light' ? 'حالت تیره' : 'حالت روشن'}
          </button>
          <span className="user-chip">{user}</span>
          <button className="btn ghost" onClick={logout}>خروج</button>
        </div>
      </header>
      <main className="content">
        {tab === 'dashboard' ? <Dashboard onOpenQueue={() => setTab('alerts')} /> : <AlertQueue currentUser={user} />}
      </main>
    </div>
  );
}
