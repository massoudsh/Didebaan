import { useState } from 'react';
import { login } from '../api.js';

export default function Login({ onLogin }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  async function submit(event) {
    event.preventDefault();
    setBusy(true);
    setError('');
    try {
      await login(username.trim(), password);
      onLogin(username.trim());
    } catch (err) {
      setError(err.status === 400 ? 'نام کاربری یا گذرواژه نادرست است.' : err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="login-wrap">
      <form className="login-card" onSubmit={submit}>
        <span className="brand-mark large" aria-hidden="true">د</span>
        <h1>ورود به دیده‌بان</h1>
        <p className="muted">مرکز بررسی هشدارهای تقلب و انطباق</p>
        <label>
          نام کاربری
          <input value={username} onChange={(e) => setUsername(e.target.value)} autoComplete="username" required autoFocus dir="ltr" />
        </label>
        <label>
          گذرواژه
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="current-password" required dir="ltr" />
        </label>
        {error && <p className="error" role="alert">{error}</p>}
        <button className="btn primary" disabled={busy}>{busy ? 'در حال ورود…' : 'ورود'}</button>
      </form>
    </div>
  );
}
